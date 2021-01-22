
PACKAGE_NAME := lib3to6

# This is the python version that is used for:
# - `make fmt`
# - `make ipy`
# - `make lint`
# - `make devtest`
DEVELOPMENT_PYTHON_VERSION := python=3.9

# These must be valid (space separated) conda package names.
# A separate conda environment will be created for each of these.
#
# These are the interpreters we use to test that the output of lib3to6 works
# with that version. The interpreter used to run lib3to6 and produce that output
# is the DEVELOPMENT_PYTHON_VERSION.
SUPPORTED_PYTHON_VERSIONS := python=3.9 python=3.8 python=3.7 python=3.6 pypy3.6 pypy3.5 python=2.7


include Makefile.bootstrapit.make

## -- Extra/Custom/Project Specific Tasks --

ENV_CPY36 := $(ENV_PREFIX)/lib3to6_py36/bin/python
ENV_PYPY36 := $(ENV_PREFIX)/lib3to6_pypy36/bin/pypy3

## Run transpile on test_project
.PHONY: integration_test
integration_test:
	@rm -rf integration_test_dist/;
	@rm -rf test_project/dist/;

	@# self test with python 3.6
	@$(ENV_CPY36) setup.py bdist_wheel --dist-dir=integration_test_dist --python-tag=py36.py37.py38;
	@$(ENV_CPY36) -m pip install -U integration_test_dist/lib3to6*.whl;
	@$(ENV_CPY36) -c "from lib3to6 import packaging"

	@rm -rf integration_test_dist/;

	@# self test with PyPy 3.6
	@$(ENV_PYPY36) setup.py bdist_wheel --dist-dir=integration_test_dist --python-tag=py36.py37.py38;
	@$(ENV_PYPY36) -m pip install -U integration_test_dist/lib3to6*.whl;
	@$(ENV_PYPY36) -c "from lib3to6 import packaging"

	@rm -rf integration_test_dist/;

	@# test project with python 3.8+
	@$(DEV_ENV_PY) setup.py bdist_wheel --dist-dir=integration_test_dist --python-tag=py36.py37.py38;
	@$(DEV_ENV_PY) -m pip install -U integration_test_dist/lib3to6*.whl;
	@$(DEV_ENV_PY) -c "from lib3to6 import packaging"

	@bash -c "cd test_project && $(DEV_ENV_PY) setup.py bdist_wheel --python-tag=py2.py3" \

	@IFS=' ' read -r -a env_py_paths <<< "$(CONDA_ENV_BIN_PYTHON_PATHS)"; \
	for i in $${!env_py_paths[@]}; do \
		env_py=$${env_py_paths[i]}; \
		echo "Testing on "$$($${env_py} --version); \
		$${env_py} -m pip uninstall -y test-module; \
		$${env_py} -m pip install test_project/dist/test_module*.whl; \
		$${env_py} -c "import test_module" | grep "all ok"; \
	done;
