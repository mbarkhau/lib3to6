"""
I initially didn't think of how to rewrite the expansions as an
expression, so I thought I would have to manipulate the parent
block by adding these hiddious temporary variables.

a = [*[1, 2, *[3, 4], 5], 6]

upg_args_0 = []
upg_args_1 = []
upg_args_1.append(1)
upg_args_1.append(2)
upg_args_1.extend([3, 4])
upg_args_1.append(5)
upg_args_0.extend(upg_args_1)
del upg_args_1
upg_args_0.append(6)
a = upg_args_0
del upg_args_0
"""

ArgUnpackNodes = (ast.Call, ast.List, ast.Tuple, ast.Set)
ArgUnpackType = typ.Union[ast.Call, ast.List, ast.Tuple, ast.Set]
KwArgUnpackNodes = (ast.Call, ast.Dict)
KwArgUnpackType = typ.Union[ast.Call, ast.Dict]


ValNodeUpdate = typ.Tuple[typ.List[ast.stmt], ast.expr, typ.List[ast.Delete]]
ListFieldNodeUpdate = typ.Tuple[typ.List[ast.stmt], typ.List[ast.expr], typ.List[ast.Delete]]
ExpandedUpdate = typ.Tuple[typ.List[ast.stmt], typ.List[ast.Delete]]


class BlockNode:

    body: typ.List[ast.stmt]


STMTLIST_FIELD_NAMES = {"body", "orelse", "finalbody"}


def node_field_sort_key(elem):
    # NOTE (mb 2018-06-23): Expand block bodies before
    #   node expressions There's no particular reason to
    #   do this other than making things predictable (and
    #   testable).
    field_name, field = elem
    return (field_name not in STMTLIST_FIELD_NAMES, field_name)


class V1UnpackingGeneralizationsFixer(FixerBase):

    version_info = VersionInfo(
        apply_since="2.0",
        apply_until="3.4",
    )

    def expand_starargs(self, node: ArgUnpackType):
        container_types = (ast.List, ast.Set, ast.Tuple)
        ContainerNode = typ.Union[ast.List, ast.Set, ast.Tuple]

        if isinstance(node, ast.Call):
            elts = node.args
        elif isinstance(node, container_types):
            elts = node.elts
        else:
            raise TypeError(f"Unexpected node: {node}")

        # leaf_node =
        # leaf_elts
        new_elts = []
        list_concats = []
        for arg in elts:
            if isinstance(arg, ast.Starred):
                if isinstance(arg, ast.List):
                    new_elts.extend(arg.elts)
                else:
                    list_concats.append(new_elts)
                    new_elts = []
                    list_concats.append(arg)
                    # new_elts.append(arg.elts)
                    pass

        root_value_node = ast.List(elts=[])
        leaf_value_node = root_value_node

        if isinstance(node, (ast.Call, ast.Set, ast.Tuple)):
            if isinstance(node, ast.Set):
                node_func = "set"
            elif isinstance(node, ast.Tuple):
                node_func = "tuple"
            else:
                assert isinstance(node, ast.Call)
                node_func = node.func

            target = ast.Call(
                func=node_func,
                args=[ast.Starred(
                    value=root_value_node,
                    ctx=ast.Load(),
                )],
                keywords=node.keywords,
            )
        else:
            assert isinstance(node, ast.List)
            target = root_value_node

    def __call__(self, cfg: common.BuildConfig, tree: ast.Module) -> ast.Module:
        return tree
        walker = astor.TreeWalk()
        for node in walker.walk(tree):
            if isinstance(node, ArgUnpackNodes) and self._has_stararg_g12n(node):
                self.expand_starargs(node)
                print("*", utils.dump_ast(node))
            elif isinstance(node, KwArgUnpackNodes) and self._has_starstarargs_g12n(node):
                print("**", node)
        return tree


def is_block_field(field_name: str, field: typ.Any) -> bool:
    return field_name in STMTLIST_FIELD_NAMES and isinstance(field, list)


def make_temp_lambda_as_def(
    lambda_node: ast.Lambda, body: typ.List[ast.stmt], name="temp_lambda_as_def"
) -> ast.FunctionDef:
    body.append(ast.Return(value=lambda_node.body))
    return ast.FunctionDef(name=name, args=lambda_node.args, body=body, decorator_list=[])


class V0UnpackingGeneralizationsFixer(FixerBase):

    version_info = VersionInfo(
        apply_since="2.0",
        apply_until="3.4",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._tmp_var_index = 0

    def _has_stararg_g12n(self, val_node: ast.expr) -> bool:
        if isinstance(val_node, ast.Call):
            elts = val_node.args
        elif isinstance(val_node, (ast.List, ast.Tuple, ast.Set)):
            elts = val_node.elts
        else:
            raise TypeError(f"Unexpected val_node: {val_node}")

        has_starred_arg = False
        for arg in elts:
            # Anything after * means we have to apply the fix
            if has_starred_arg:
                return True
            has_starred_arg = isinstance(arg, ast.Starred)
        return False

    def _has_starstarargs_g12n(self, val_node: ast.expr) -> bool:
        if isinstance(val_node, ast.Call):
            has_kwstarred_arg = False
            for kw in val_node.keywords:
                if has_kwstarred_arg:
                    # Anything after ** means we have to apply the fix
                    return True
                has_kwstarred_arg = kw.arg is None
            return False
        elif isinstance(val_node, ast.Dict):
            has_kwstarred_arg = False
            for key in val_node.keys:
                if has_kwstarred_arg:
                    # Anything after ** means we have to apply the fix
                    return True
                has_kwstarred_arg = key is None
            return False
        else:
            raise TypeError(f"Unexpected val_node: {val_node}")

    def expand_args_unpacking(self, val_node: ArgUnpackType) -> ValNodeUpdate:
        upg_args_name = f"upg_args_{self._tmp_var_index}"
        upg_args_name_node = ast.Name(id=upg_args_name, ctx=ast.Load())
        self._tmp_var_index += 1

        if not isinstance(val_node, (ast.Call, ast.List, ast.Set, ast.Tuple)):
            raise TypeError(f"Unexpected val_node: {val_node}")

        container_types = (ast.List, ast.Set, ast.Tuple)
        ContainerNode = typ.Union[ast.List, ast.Set, ast.Tuple]

        if isinstance(val_node, ast.Call):
            val_node_elts = val_node.args
        elif isinstance(val_node, container_types):
            val_node_elts = val_node.elts

        upg_args_initializer: ContainerNode

        if isinstance(val_node, (ast.List, ast.Call)):
            upg_args_initializer = ast.List(elts=[], ctx=ast.Load())
        elif isinstance(val_node, ast.Tuple):
            upg_args_initializer = ast.Tuple(elts=[], ctx=ast.Load())
        elif isinstance(val_node, ast.Set):
            upg_args_initializer = ast.Set(elts=[], ctx=ast.Load())

        upg_args_assignment = ast.Assign(
            targets=[ast.Name(id=upg_args_name, ctx=ast.Store())],
            value=upg_args_initializer,
        )
        prefix_nodes: typ.List[ast.stmt] = [upg_args_assignment]
        prev_expr = upg_args_initializer
        prev_expr_elts = prev_expr.elts

        for elt in val_node_elts:
            if not isinstance(elt, ast.Starred):
                prev_expr_elts.append(elt)
                continue

            argval = elt.value
            if isinstance(argval, container_types):
                prev_expr_elts.extend(argval.elts)
            elif isinstance(argval, ast.Name):
                if isinstance(val_node, (ast.List, ast.Call)):
                    prev_expr = ast.List(elts=[], ctx=ast.Load())
                elif isinstance(val_node, ast.Tuple):
                    prev_expr = ast.Tuple(elts=[], ctx=ast.Load())
                elif isinstance(val_node, ast.Set):
                    prev_expr = ast.Set(elts=[], ctx=ast.Load())
            else:
                raise TypeError(f"Unexpected argval: {argval}")

            # func_node = ast.Attribute(
            #     value=ast.Name(id=upg_args_name, ctx=ast.Load()),
            #     attr=func_name,
            #     ctx=ast.Load(),
            # )
            # prefix_nodes.append(ast.Expr(
            #     value=ast.Call(func=func_node, args=args, keywords=[])
            # ))

        if len(prefix_nodes) == 1:
            return [], upg_args_initializer, []

        new_val_node: ast.expr

        if isinstance(val_node, ast.Call):
            new_val_node = ast.Call(
                func=val_node.func,
                args=[ast.Starred(
                    value=upg_args_name_node,
                    ctx=ast.Load(),
                )],
                keywords=val_node.keywords,
            )
        else:
            new_val_node = upg_args_name_node

        del_node = ast.Delete(targets=[ast.Name(id=upg_args_name, ctx=ast.Del())])
        return prefix_nodes, new_val_node, [del_node]

    def expand_kwargs_unpacking(self, val_node: KwArgUnpackType) -> ValNodeUpdate:
        upg_kwargs_name = f"upg_kwargs_{self._tmp_var_index}"
        self._tmp_var_index += 1

        prefix_nodes: typ.List[ast.stmt] = [
            ast.Assign(
                targets=[ast.Name(id=upg_kwargs_name, ctx=ast.Store())],
                value=ast.Dict(keys=[], values=[], ctx=ast.Load()),
            )
        ]

        def add_items(val_node_items: typ.Iterable[typ.Tuple]):
            for key, val in val_node_items:
                if key is None:
                    prefix_nodes.append(ast.Expr(value=ast.Call(
                        func=ast.Attribute(
                            value=ast.Name(id=upg_kwargs_name, ctx=ast.Load()),
                            attr="update",
                            ctx=ast.Load(),
                        ),
                        args=[val],
                        keywords=[],
                    )))
                else:
                    if isinstance(key, ast.Str):
                        key_val = key
                    elif isinstance(key, str):
                        key_val = ast.Str(s=key)
                    else:
                        raise TypeError(f"Invalid dict key {key}")

                    prefix_nodes.append(ast.Assign(targets=[
                        ast.Subscript(
                            slice=ast.Index(value=key_val),
                            value=ast.Name(id=upg_kwargs_name, ctx=ast.Load()),
                            ctx=ast.Store(),
                        ),
                    ], value=val))

        if isinstance(val_node, ast.Call):
            add_items((kw.arg, kw.value) for kw in val_node.keywords)
            args = val_node.args
            replacenemt_func = val_node.func
        elif isinstance(val_node, ast.Dict):
            args = []
            add_items(zip(val_node.keys, val_node.values))
            replacenemt_func = ast.Name(id="dict", ctx=ast.Load())
        else:
            raise TypeError(f"Unexpected val_node: {val_node}")

        new_val_node = ast.Call(
            func=replacenemt_func,
            args=args,
            keywords=[ast.keyword(
                arg=None, value=ast.Name(id=upg_kwargs_name, ctx=ast.Load())
            )],
        )
        del_node = ast.Delete(targets=[ast.Name(id=upg_kwargs_name, ctx=ast.Del())])
        return prefix_nodes, new_val_node, [del_node]

    def make_val_node_update(self, val_node: ast.expr) -> typ.Optional[ValNodeUpdate]:
        all_prefix_nodes: typ.List[ast.stmt] = []
        all_del_nodes: typ.List[ast.Delete] = []

        if isinstance(val_node, ArgUnpackNodes) and self._has_stararg_g12n(val_node):
            prefix_nodes, new_val_node, del_nodes = self.expand_args_unpacking(val_node)
            assert not (
                isinstance(new_val_node, ArgUnpackNodes) and
                self._has_stararg_g12n(new_val_node)
            )
            all_prefix_nodes.extend(prefix_nodes)
            val_node = new_val_node
            all_del_nodes.extend(del_nodes)

        if isinstance(val_node, KwArgUnpackNodes) and self._has_starstarargs_g12n(val_node):
            prefix_nodes, new_val_node, del_nodes = self.expand_kwargs_unpacking(val_node)
            assert not (
                isinstance(new_val_node, KwArgUnpackNodes) and
                self._has_starstarargs_g12n(new_val_node)
            )
            all_prefix_nodes.extend(prefix_nodes)
            val_node = new_val_node
            all_del_nodes.extend(del_nodes)

        if len(all_prefix_nodes) > 0:
            assert len(all_del_nodes) > 0
        return all_prefix_nodes, val_node, all_del_nodes

    def make_single_field_update(
        self, field_node: ast.expr
    ) -> typ.Optional[ValNodeUpdate]:

        if isinstance(field_node, ArgUnpackNodes + KwArgUnpackNodes):
            val_node_update = self.make_val_node_update(field_node)
            if val_node_update is not None:
                return val_node_update

        all_prefix_nodes: typ.List[ast.stmt] = []
        all_del_nodes: typ.List[ast.Delete] = []

        sub_fields = sorted(ast.iter_fields(field_node), key=node_field_sort_key)
        for sub_field_name, sub_field in sub_fields:
            # NOTE (mb 2018-06-23): field nodes should not have any body
            assert not is_block_field(sub_field_name, sub_field), f"""
            Unexpected block field {sub_field_name} for {field_node}
            """.strip()

            if not isinstance(sub_field, (list, ast.AST)):
                continue

            maybe_body_update = self.make_field_update(field_node, sub_field_name, sub_field)

            if maybe_body_update is None:
                continue

            prefix_nodes, del_nodes = maybe_body_update

            if isinstance(field_node, ast.Lambda):
                # NOTE (mb 2018-06-24): An update inside a lambda can reference
                #   parameters of the lambda. This means the prefix_nodes
                #   would carry over those references. So we convert the
                #   lambda to a temporary FunctionDef and replace it with
                #   a reference to that function def.
                temp_func_def = make_temp_lambda_as_def(field_node, prefix_nodes)
                all_prefix_nodes.append(temp_func_def)
                field_node = ast.Name(id=temp_func_def.name, ctx=ast.Load())
                all_del_nodes.append(ast.Delete(targets=[
                    ast.Name(id=temp_func_def.name, ctx=ast.Del())
                ]))
            else:
                all_prefix_nodes.extend(prefix_nodes)
                all_del_nodes.extend(del_nodes)

        if len(all_prefix_nodes) > 0:
            assert len(all_del_nodes) > 0

        return all_prefix_nodes, field_node, all_del_nodes

    def make_list_field_update(
        self, field_nodes: typ.List[ast.expr]
    ) -> typ.Optional[ListFieldNodeUpdate]:
        if len(field_nodes) == 0:
            return None

        all_prefix_nodes: typ.List[ast.stmt] = []
        new_field_nodes: typ.List[ast.expr] = []
        all_del_nodes: typ.List[ast.Delete] = []

        for field_node in field_nodes:
            body_update = self.make_single_field_update(field_node)
            if body_update is None:
                new_field_nodes.append(field_node)
            else:
                prefix_nodes, new_field, del_nodes = body_update
                all_prefix_nodes.extend(prefix_nodes)
                new_field_nodes.append(new_field)
                all_del_nodes.extend(del_nodes)

        if len(all_prefix_nodes) > 0:
            assert len(all_del_nodes) > 0
            assert len(new_field_nodes) > 0
            assert len(new_field_nodes) == len(field_nodes)

        return all_prefix_nodes, new_field_nodes, all_del_nodes

    def make_field_update(
        self, parent_node, field_name, field
    ) -> typ.Optional[ExpandedUpdate]:
        maybe_body_update: typ.Union[ListFieldNodeUpdate, ValNodeUpdate, None]

        if isinstance(field, list):
            maybe_body_update = self.make_list_field_update(field)
        else:
            maybe_body_update = self.make_single_field_update(field)

        if maybe_body_update is None:
            return None

        if isinstance(field, list):
            prefix_nodes, new_list_field, del_nodes = maybe_body_update
            setattr(parent_node, field_name, new_list_field)
        else:
            prefix_nodes, new_field, del_nodes = maybe_body_update
            setattr(parent_node, field_name, new_field)

        if len(prefix_nodes) > 0:
            assert len(del_nodes) > 0
            return prefix_nodes, del_nodes
        else:
            return None

    def apply_body_updates(self, body: typ.List[ast.stmt]):
        initial_len_body = len(body)
        prev_len_body = -1
        while prev_len_body != len(body):
            if len(body) > initial_len_body * 100:
                # NOTE (mb 2018-06-23): This should never happen,
                #   so it's an internal error, but rather than
                #   running out of memory, an early exception is
                #   raised.
                raise Exception("Expansion overflow")

            prev_len_body = len(body)

            o = 0
            # NOTE (mb 2018-06-17): Copy the body, because we
            #   modify it during iteration.
            body_copy = list(body)
            for i, node in enumerate(body_copy):
                fields = sorted(ast.iter_fields(node), key=node_field_sort_key)
                for field_name, field in fields:
                    if not isinstance(field, (list, ast.AST)):
                        continue

                    if is_block_field(field_name, field):
                        node_body = typ.cast(typ.List[ast.stmt], field)
                        self.apply_body_updates(node_body)
                        continue

                    maybe_body_update = self.make_field_update(node, field_name, field)

                    if maybe_body_update is None:
                        continue

                    prefix_nodes, del_nodes = maybe_body_update

                    body[i + o:i + o] = prefix_nodes
                    o += len(prefix_nodes)
                    if isinstance(body[i + o], ast.Return):
                        continue

                    # NOTE (mb 2018-06-24): We don't need to del if
                    #   we're at the end of a function block anyway.
                    o += 1
                    body[i + o:i + o] = del_nodes

    def __call__(self, cfg: common.BuildConfig, tree: ast.Module) -> ast.Module:
        self.apply_body_updates(tree.body)
        return tree
