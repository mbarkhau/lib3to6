
PACKAGE_NAME := lib3to6

# This is the python version that is used for:
# - `make fmt`
# - `make ipy`
# - `make lint`
# - `make devtest`
DEVELOPMENT_PYTHON_VERSION := python=3.8

# These must be valid (space separated) conda package names.
# A separate conda environment will be created for each of these.
#
# Some valid options are:
# - python=2.7
# - python=3.5
# - python=3.6
# - python=3.7
# - pypy2.7
# - pypy3.5
SUPPORTED_PYTHON_VERSIONS := python=3.8 python=3.7 python=3.6 python=2.7 pypy3.5


include makefile.bootstrapit.make

## -- Extra/Custom/Project Specific Tasks --

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
