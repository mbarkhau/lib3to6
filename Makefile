.PHONY: setup_conda_envs install \
	test devtest fulltest lint \
	clean rm_site_packages \
	build readme upload


build/.setup_conda_envs.make_marker:
	conda create --name lib3to6_37 python=3.7 --yes
	conda create --name lib3to6_36 python=3.6 --yes
	conda create --name lib3to6_27 python=2.7 --yes
	@mkdir -p build/
	@touch build/.setup_conda_envs.make_marker


build/envs.txt: build/.setup_conda_envs.make_marker
	@mkdir -p build/
	conda env list | grep lib3to6 | rev | cut -d " " -f1 | rev > build/envs.txt.tmp
	mv build/envs.txt.tmp build/envs.txt


PYENV37 ?= $(shell bash -c "grep 37 build/envs.txt || true")
PYENV36 ?= $(shell bash -c "grep 36 build/envs.txt || true")
PYENV27 ?= $(shell bash -c "grep 27 build/envs.txt || true")
PYTHON37 ?= $(PYENV37)/bin/python
PYTHON36 ?= $(PYENV36)/bin/python
PYTHON27 ?= $(PYENV27)/bin/python

BDIST_WHEEL_LIB3TO6 = $(shell bash -c "ls -1t dist/lib3to6*py2*.whl | head -n 1")
SDIST_LIB3TO6 = $(shell bash -c "ls -1t dist/lib3to6*.tar.gz | head -n 1")
DIST_WHEEL_TEST = $(shell bash -c "ls -1t test_project/dist/*py2*.whl | head -n 1")
BUILD_LOG_DIR = "test_build_logs/"
BUILD_LOG_FILE := $(shell date +"$(BUILD_LOG_DIR)%Y%m%dt%H%M%S%N.log")


build/.install.make_marker: setup.py build/envs.txt
	$(PYTHON36) -m pip install --upgrade --quiet \
		pip setuptools wheel twine \
		flake8 mypy typing-extensions \
		rst2html5 \
		pytest pytest-cov \
		ipython pudb \
		astor pathlib2 click;

	$(PYTHON37) -m pip install --upgrade --quiet pip setuptools wheel astor;
	$(PYTHON36) -m pip install --upgrade --quiet pip setuptools wheel astor;
	$(PYTHON27) -m pip install --upgrade --quiet pip setuptools wheel astor;

	@mkdir -p build/
	@touch build/.install.make_marker


clean:
	rm -f build/envs.txt
	rm -f build/.setup_conda_envs.make_marker
	rm -f build/.install.make_marker


# NOTE (mb 2018-08-23): The linter has an issue running with
# 	python 3.7 because some code in pycodestyle=2.3.1
#	but we have to wait for a flake8 update because
#	reasons... https://github.com/PyCQA/pycodestyle/issues/728


lint: build/.install.make_marker
	@echo -n "lint.."
	@$(PYTHON36) -m flake8 src/lib3to6/
	@echo "ok"


mypy: build/.install.make_marker
	@echo -n "mypy.."
	@MYPYPATH=stubs/ $(PYTHON36) -m mypy \
		src/lib3to6/
	@echo "ok"


test: build/.install.make_marker
	@PYTHONPATH=src/:$$PYTHONPATH \
		$(PYTHON36) -m pytest \
		--cov-report html \
		--cov=lib3to6 \
		test/


devtest: build/.install.make_marker
	PYTHONPATH=src/:$$PYTHONPATH \
		$(PYTHON36) -m pytest -v \
		--cov-report term \
		--cov=lib3to6 \
		--capture=no \
		--exitfirst \
		test/


build/.coverage_percent.txt: test
	@mkdir -p build/
	@grep -oP '>[0-9]+%</td>' htmlcov/index.html \
		| head -n 1 \
		| grep -oP '[.0-9]+' \
		> build/.coverage_percent.txt


README.rst: build/.coverage_percent.txt
	@sed -i "s/coverage-[0-9]*/coverage-$$(cat build/.coverage_percent.txt)/" README.rst


build/README.html: build/.install.make_marker README.rst CHANGELOG.rst
	@cat README.rst > build/.full_readme.rst
	@echo "\n" >> build/.full_readme.rst
	@cat CHANGELOG.rst >> build/.full_readme.rst
	@$(PYENV36)/bin/rst2html5 --strict \
		build/.full_readme.rst > build/README.html.tmp
	@mv build/README.html.tmp build/README.html
	@echo "updated build/README.html"


bump_version:
	date +"v%Y%m." > .new_version.txt
	awk 'match($$0, /v[0-9]+.([0-9]+)(-[a-z]*)?/, arr) { printf "%04d%s\n", (arr[1]+1), arr[2] }' \
		version.txt >> .new_version.txt
	sed -i -z 's/\n//g' .new_version.txt
	cat version.txt >> old_versions.txt
	mv .new_version.txt version.txt
	sed -i "s/__version__ = \".*\"/__version__ = \"$$(cat version.txt)\"/" setup.py
	sed -i "s/__version__ = \".*\"/__version__ = \"$$(cat version.txt)\"/" \
		src/lib3to6/__init__.py
	sed -i "s/CalVer-.*-blue.svg/CalVer-$$(cat version.txt | sed 's/-/--/')-blue.svg/" \
		README.rst
	sed -i "s/CalVer .*/CalVer $$(cat version.txt)/" README.rst


readme: build/README.html


build/.src_files.txt: setup.py build/envs.txt src/lib3to6/*.py
	@mkdir -p build/
	@ls -l setup.py build/envs.txt src/lib3to6/*.py > build/.src_files.txt.tmp
	@mv build/.src_files.txt.tmp build/.src_files.txt


rm_site_packages:
	rm -rf $(PYENV36)/lib/python3.6/site-packages/lib3to6/
	rm -rf $(PYENV36)/lib/python3.6/site-packages/lib3to6*.dist-info/
	rm -rf $(PYENV36)/lib/python3.6/site-packages/lib3to6*.egg-info/
	rm -f $(PYENV36)/lib/python3.6/site-packages/lib3to6*.egg


build/.local_install.make_marker: build/.src_files.txt rm_site_packages
	@echo "installing lib3to6.."
	@$(PYTHON36) setup.py install --no-compile --verbose
	@mkdir -p build/
	@$(PYTHON36) -c "import lib3to6"
	@echo "install completed for lib3to6"
	@touch build/.local_install.make_marker


build: build/.local_install.make_marker
	@mkdir -p $(BUILD_LOG_DIR)
	@echo "writing full build log to $(BUILD_LOG_FILE)"
	@echo "building lib3to6.."
	@$(PYTHON36) setup.py bdist_wheel --python-tag=py2.py3 >> $(BUILD_LOG_FILE)
	@echo "build completed for lib3to6"


upload: build/.install.make_marker build/README.html
	$(PYTHON36) setup.py bdist_wheel --python-tag=py2.py3
	$(PYENV36)/bin/twine upload $(BDIST_WHEEL_LIB3TO6)


fulltest: build/.install.make_marker build/README.html lint mypy test build
	@echo -n "envcheck.."
	@echo -n "py27.."
	@$(PYTHON27) --version 2>&1 | grep "Python 2.7" >> $(BUILD_LOG_FILE)
	@echo -n "ok "

	@echo -n "py37.."
	@$(PYTHON37) --version 2>&1 | grep "Python 3.7" >> $(BUILD_LOG_FILE)
	@echo -n "ok "

	@echo -n "py36.."
	@$(PYTHON36) --version 2>&1 | grep "Python 3.6" >> $(BUILD_LOG_FILE)
	@echo -n "ok "

	@echo -n "install.."
	@$(PYTHON37) -m pip install  --ignore-installed --quiet --force \
		$(BDIST_WHEEL_LIB3TO6) >> $(BUILD_LOG_FILE)
	@echo "ok"

	@echo -n "build test_project.."
	@bash -c "cd test_project;$(PYTHON37) setup.py bdist_wheel --python-tag=py2.py3" \
		>> $(BUILD_LOG_FILE)
	@echo "ok"

	@echo -n "py27.."
	@$(PYTHON27) -m pip install --ignore-installed --quiet --force \
		$(DIST_WHEEL_TEST) >> $(BUILD_LOG_FILE)
	@echo -n "installed.."
	@$(PYTHON27) -c "import test_module" | grep "all ok" >> $(BUILD_LOG_FILE)
	@echo "ok"

	@echo -n "py37.."
	@$(PYTHON37) -m pip install --ignore-installed --quiet --force \
		$(DIST_WHEEL_TEST) >> $(BUILD_LOG_FILE)
	@echo -n "installed.."
	@$(PYTHON37) -c "import test_module" | grep "all ok" >> $(BUILD_LOG_FILE)
	@echo "ok"

	@echo -n "py36.."
	@$(PYTHON36) -m pip install --ignore-installed --quiet --force \
		$(DIST_WHEEL_TEST) >> $(BUILD_LOG_FILE)
	@echo -n "installed.."
	@$(PYTHON36) -c "import test_module" | grep "all ok" >> $(BUILD_LOG_FILE)
	@echo "ok"

	@wait


setup_conda_envs: build/.setup_conda_envs.make_marker

install: build/.install.make_marker

run_main:
	PYTHONPATH=src/:$$PYTHONPATH $(PYTHON36) -m lib3to6 --help
