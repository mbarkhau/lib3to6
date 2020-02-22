
## Run transpile on test_project
.PHONY: integration_test
integration_test:
	@rm -rf integration_test_dist/;
	@rm -rf test_project/dist/;

	@$(DEV_ENV_PY) setup.py bdist_wheel --dist-dir=integration_test_dist --python-tag=py36.py37.py38;
	@$(DEV_ENV_PY) -m pip install -U integration_test_dist/lib3to6*.whl;
	@bash -c "cd test_project && $(DEV_ENV_PY) setup.py bdist_wheel --python-tag=py2.py3" \

	@IFS=' ' read -r -a env_py_paths <<< "$(CONDA_ENV_BIN_PYTHON_PATHS)"; \
	for i in $${!env_py_paths[@]}; do \
		env_py=$${env_py_paths[i]}; \
		echo "Testing on "$$($${env_py} --version); \
		$${env_py} -m pip install test_project/dist/test_module*.whl; \
		$${env_py} -c "import test_module" | grep "all ok"; \
	done;
