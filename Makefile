.PHONY: clean test devtest fulltest lint setup_conda_envs install_all install_dev build upload

.setup_conda_envs.make_marker:
	conda create --name three2six37 python=3.7 --yes
	conda create --name three2six36 python=3.6 --yes
	conda create --name three2six35 python=3.5 --yes
	conda create --name three2six34 python=3.4 --yes
	conda create --name three2six27 python=2.7 --yes
	@touch .setup_conda_envs.make_marker


envs.txt: .setup_conda_envs.make_marker
	conda env list | grep three2six | rev | cut -d " " -f1 | rev > envs.txt.tmp
	mv envs.txt.tmp envs.txt


PYENV37 ?= $(shell bash -c "grep three2six37 envs.txt || true")
PYENV36 ?= $(shell bash -c "grep three2six36 envs.txt || true")
PYENV35 ?= $(shell bash -c "grep three2six35 envs.txt || true")
PYENV34 ?= $(shell bash -c "grep three2six34 envs.txt || true")
PYENV27 ?= $(shell bash -c "grep three2six27 envs.txt || true")
PYTHON37 ?= $(PYENV37)/bin/python
PYTHON36 ?= $(PYENV36)/bin/python
PYTHON35 ?= $(PYENV35)/bin/python
PYTHON34 ?= $(PYENV34)/bin/python
PYTHON27 ?= $(PYENV27)/bin/python

DIST_WHEEL_THREE2SIX = $(shell bash -c "ls -1t dist/*py2*.whl | head -n 1")
DIST_WHEEL_TEST = $(shell bash -c "ls -1t test_project/dist/*py2*.whl | head -n 1")
BUILD_LOG := $(shell date +"test_build_logs/%Y%m%dt%H%M%S%N.log")


.install_dev.make_marker: setup.py envs.txt
	$(PYTHON37) -m pip install --upgrade --quiet \
		pip wheel twine \
		flake8 mypy typing-extensions \
		rst2html5 \
		pytest pytest-cov \
		ipython pudb \
		astor pathlib2 click;
	@touch .install_dev.make_marker


.install_all.make_marker: setup.py envs.txt .install_dev.make_marker
	$(PYTHON37) -m pip install --upgrade --quiet pip wheel astor;
	$(PYTHON36) -m pip install --upgrade --quiet pip wheel astor;
	$(PYTHON35) -m pip install --upgrade --quiet pip wheel astor;
	$(PYTHON34) -m pip install --upgrade --quiet pip wheel astor;
	$(PYTHON27) -m pip install --upgrade --quiet pip wheel astor;
	@touch .install_all.make_marker

clean:
	rm -f envs.txt
	rm -f .setup_conda_envs.make_marker
	rm -f .install_all.make_marker
	rm -f .install_dev.make_marker


lint: .install_dev.make_marker
	@echo -n "lint.."
	@$(PYTHON36) -m flake8 src/three2six/
	@echo "ok"


mypy: .install_dev.make_marker
	@echo -n "mypy.."
	@MYPYPATH=stubs/ $(PYTHON37) -m mypy \
		src/three2six/
	@echo "ok"


test: .install_dev.make_marker
	@PYTHONPATH=src/:$$PYTHONPATH \
		$(PYTHON37) -m pytest \
		--cov-report html \
		--cov=three2six \
		tests/


devtest: .install_dev.make_marker
	PYTHONPATH=src/:$$PYTHONPATH \
		$(PYTHON37) -m pytest -v \
		--cov-report term \
		--cov=three2six \
		--capture=no \
		--exitfirst \
		tests/


.coverage_percent.txt: test
	@grep -oP '>[0-9]+%</td>' htmlcov/index.html \
		| head -n 1 \
		| grep -oP '[.0-9]+' \
		> .coverage_percent.txt


README.rst: .coverage_percent.txt
	sed -i "s/coverage-[0-9]*/coverage-$$(cat .coverage_percent.txt)/" README.rst


README.html: .install_dev.make_marker README.rst
	$(PYENV37)/bin/rst2html5 --strict README.rst > README.html.tmp
	mv README.html.tmp README.html


build:
	@mkdir -p test_build_logs/
	@echo "Writing full build log to $(BUILD_LOG)"
	@echo -n "build three2six.."
	# NOTE (mb 2018-07-08): Before we can run setup.py we
	# 	need a valid install of the previous version.
	# TODO (mb 2018-07-08): How to bootstrap new devs?
	# TODO (mb 2018-07-12): Generate multiple builds,
	#	one for each supported version.
	$(PYTHON37) -m pip uninstall three2six --yes
	$(PYTHON37) -m pip install --ignore-installed --force .
	@$(PYTHON37) setup.py bdist_wheel --python-tag=py2.py3 >> $(BUILD_LOG)
	@echo "ok"


upload: .install_dev.make_marker README.html
	$(PYTHON37) setup.py bdist_wheel --python-tag=py2.py3 upload


fulltest: .install_all.make_marker README.html lint mypy test build
	@echo -n "envcheck.."
	@echo -n "py27.."
	@$(PYTHON27) --version 2>&1 | grep "Python 2.7" >> $(BUILD_LOG)
	@echo -n "ok "

	@echo -n "py37.."
	@$(PYTHON37) --version 2>&1 | grep "Python 3.7" >> $(BUILD_LOG)
	@echo -n "ok "

	@echo -n "py36.."
	@$(PYTHON36) --version 2>&1 | grep "Python 3.6" >> $(BUILD_LOG)
	@echo -n "ok "

	@echo -n "py35.."
	@$(PYTHON35) --version 2>&1 | grep "Python 3.5" >> $(BUILD_LOG)
	@echo -n "ok "

	@echo -n "py34.."
	@$(PYTHON34) --version 2>&1 | grep "Python 3.4" >> $(BUILD_LOG)
	@echo "ok"

	@echo -n "install.."
	@$(PYTHON37) -m pip install  --ignore-installed --quiet --force \
		$(DIST_WHEEL_THREE2SIX) >> $(BUILD_LOG)
	@echo "ok"

	@echo -n "build test_project.."
	@bash -c "cd test_project;$(PYTHON37) setup.py bdist_wheel --python-tag=py2.py3" >> $(BUILD_LOG)
	@echo "ok"

	@echo -n "py27.."
	@$(PYTHON27) -m pip install --ignore-installed --quiet --force \
		$(DIST_WHEEL_TEST) >> $(BUILD_LOG)
	@echo -n "installed.."
	@$(PYTHON27) -c "import test_module" | grep "all ok" >> $(BUILD_LOG)
	@echo "ok"

	@echo -n "py37.."
	@$(PYTHON37) -m pip install --ignore-installed --quiet --force \
		$(DIST_WHEEL_TEST) >> $(BUILD_LOG)
	@echo -n "installed.."
	@$(PYTHON37) -c "import test_module" | grep "all ok" >> $(BUILD_LOG)
	@echo "ok"

	@echo -n "py36.."
	@$(PYTHON36) -m pip install --ignore-installed --quiet --force \
		$(DIST_WHEEL_TEST) >> $(BUILD_LOG)
	@echo -n "installed.."
	@$(PYTHON36) -c "import test_module" | grep "all ok" >> $(BUILD_LOG)
	@echo "ok"

	@echo -n "py35.."
	@$(PYTHON35) -m pip install --ignore-installed --quiet --force \
		$(DIST_WHEEL_TEST) >> $(BUILD_LOG)
	@echo -n "installed.."
	@$(PYTHON35) -c "import test_module" | grep "all ok" >> $(BUILD_LOG)
	@echo "ok"

	@echo -n "py34.."
	@$(PYTHON34) -m pip install --ignore-installed --quiet --force \
		$(DIST_WHEEL_TEST) >> $(BUILD_LOG)
	@echo -n "installed.."
	@$(PYTHON34) -c "import test_module" | grep "all ok" >> $(BUILD_LOG)
	@echo "ok"
	@wait


setup_conda_envs: .setup_conda_envs.make_marker

install_all: .install_all.make_marker

install_dev: .install_dev.make_marker

run_main:
	PYTHONPATH=src/:$$PYTHONPATH $(PYTHON36) -m three2six.main
