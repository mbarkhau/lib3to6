.PHONY: clean setup_conda_envs install \
	test devtest fulltest lint \
	readme build upload


build/.setup_conda_envs.make_marker:
	conda create --name three2six37 python=3.7 --yes
	conda create --name three2six36 python=3.6 --yes
	conda create --name three2six35 python=3.5 --yes
	conda create --name three2six34 python=3.4 --yes
	conda create --name three2six27 python=2.7 --yes
	@mkdir -p build/
	@touch build/.setup_conda_envs.make_marker


build/envs.txt: build/.setup_conda_envs.make_marker
	@mkdir -p build/
	conda env list | grep three2six | rev | cut -d " " -f1 | rev > build/envs.txt.tmp
	mv build/envs.txt.tmp build/envs.txt


PYENV37 ?= $(shell bash -c "grep three2six37 build/envs.txt || true")
PYENV36 ?= $(shell bash -c "grep three2six36 build/envs.txt || true")
PYENV35 ?= $(shell bash -c "grep three2six35 build/envs.txt || true")
PYENV34 ?= $(shell bash -c "grep three2six34 build/envs.txt || true")
PYENV27 ?= $(shell bash -c "grep three2six27 build/envs.txt || true")
PYTHON37 ?= $(PYENV37)/bin/python
PYTHON36 ?= $(PYENV36)/bin/python
PYTHON35 ?= $(PYENV35)/bin/python
PYTHON34 ?= $(PYENV34)/bin/python
PYTHON27 ?= $(PYENV27)/bin/python

DIST_WHEEL_THREE2SIX = $(shell bash -c "ls -1t dist/*py2*.whl | head -n 1")
DIST_WHEEL_TEST = $(shell bash -c "ls -1t test_project/dist/*py2*.whl | head -n 1")
BUILD_LOG_DIR = "test_build_logs/"
BUILD_LOG_FILE := $(shell date +"$(BUILD_LOG_DIR)%Y%m%dt%H%M%S%N.log")


build/.install.make_marker: setup.py build/envs.txt
	$(PYTHON37) -m pip install --upgrade --quiet \
		pip wheel twine \
		flake8 mypy typing-extensions \
		rst2html5 \
		pytest pytest-cov \
		ipython pudb \
		astor pathlib2 click;

	$(PYTHON37) -m pip install --upgrade --quiet pip wheel astor;
	$(PYTHON36) -m pip install --upgrade --quiet pip wheel astor;
	$(PYTHON35) -m pip install --upgrade --quiet pip wheel astor;
	$(PYTHON34) -m pip install --upgrade --quiet pip wheel astor;
	$(PYTHON27) -m pip install --upgrade --quiet pip wheel astor;

	@mkdir -p build/
	@touch build/.install.make_marker


clean:
	rm -f build/envs.txt
	rm -f build/.setup_conda_envs.make_marker
	rm -f build/.install.make_marker


lint: build/.install.make_marker
	@echo -n "lint.."
	@$(PYTHON36) -m flake8 src/three2six/
	@echo "ok"


mypy: build/.install.make_marker
	@echo -n "mypy.."
	@MYPYPATH=stubs/ $(PYTHON37) -m mypy \
		src/three2six/
	@echo "ok"


test: build/.install.make_marker
	@PYTHONPATH=src/:$$PYTHONPATH \
		$(PYTHON37) -m pytest \
		--cov-report html \
		--cov=three2six \
		test/


devtest: build/.install.make_marker
	PYTHONPATH=src/:$$PYTHONPATH \
		$(PYTHON37) -m pytest -v \
		--cov-report term \
		--cov=three2six \
		--capture=no \
		--exitfirst \
		test/


build/.coverage_percent.txt: test
	@grep -oP '>[0-9]+%</td>' htmlcov/index.html \
		| head -n 1 \
		| grep -oP '[.0-9]+' \
		> .coverage_percent.txt


README.rst: build/.coverage_percent.txt
	@sed -i "s/coverage-[0-9]*/coverage-$$(cat build/.coverage_percent.txt)/" README.rst


build/README.html: build/.install.make_marker README.rst CHANGELOG.rst
	@cat README.rst > build/.full_readme.rst
	@echo "\n" >> build/.full_readme.rst
	@cat CHANGELOG.rst >> build/.full_readme.rst
	@$(PYENV37)/bin/rst2html5 --strict build/.full_readme.rst > build/README.html.tmp
	@mv build/README.html.tmp build/README.html
	@echo "updated build/README.html"


readme: build/README.html


build/sources.txt: setup.py build/envs.txt src/three2six/*.py
	@mkdir -p build/
	@ls -l setup.py build/envs.txt src/three2six/*.py > build/sources.txt.tmp
	@mv build/sources.txt.tmp build/sources.txt


build/.local_install.make_marker: build/sources.txt
	@echo -n "installing three2six.."
	$(PYTHON37) -m pip uninstall three2six --yes
	$(PYTHON37) -m pip install --ignore-installed --force .
	@mkdir -p build/
	touch build/.local_install.make_marker


build: build/.local_install.make_marker
	@mkdir -p $(BUILD_LOG_DIR)
	@echo "Writing full build log to $(BUILD_LOG_FILE)"
	@echo -n "building three2six.."
	@$(PYTHON37) setup.py bdist_wheel --python-tag=py2.py3 >> $(BUILD_LOG_FILE)
	@echo "ok"


upload: build/.install.make_marker build/README.html
	$(PYTHON37) setup.py sdist bdist_wheel --python-tag=py2.py3 upload


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

	@echo -n "py35.."
	@$(PYTHON35) --version 2>&1 | grep "Python 3.5" >> $(BUILD_LOG_FILE)
	@echo -n "ok "

	@echo -n "py34.."
	@$(PYTHON34) --version 2>&1 | grep "Python 3.4" >> $(BUILD_LOG_FILE)
	@echo "ok"

	@echo -n "install.."
	@$(PYTHON37) -m pip install  --ignore-installed --quiet --force \
		$(DIST_WHEEL_THREE2SIX) >> $(BUILD_LOG_FILE)
	@echo "ok"

	@echo -n "build test_project.."
	@bash -c "cd test_project;$(PYTHON37) setup.py bdist_wheel --python-tag=py2.py3" >> $(BUILD_LOG_FILE)
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

	@echo -n "py35.."
	@$(PYTHON35) -m pip install --ignore-installed --quiet --force \
		$(DIST_WHEEL_TEST) >> $(BUILD_LOG_FILE)
	@echo -n "installed.."
	@$(PYTHON35) -c "import test_module" | grep "all ok" >> $(BUILD_LOG_FILE)
	@echo "ok"

	@echo -n "py34.."
	@$(PYTHON34) -m pip install --ignore-installed --quiet --force \
		$(DIST_WHEEL_TEST) >> $(BUILD_LOG_FILE)
	@echo -n "installed.."
	@$(PYTHON34) -c "import test_module" | grep "all ok" >> $(BUILD_LOG_FILE)
	@echo "ok"
	@wait


setup_conda_envs: build/.setup_conda_envs.make_marker

install: build/.install.make_marker

run_main:
	PYTHONPATH=src/:$$PYTHONPATH $(PYTHON36) -m three2six.main
