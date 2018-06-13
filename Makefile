.PHONY: clean test lint setup_conda_envs install_all dev_install

PYENV36 := $(shell bash -c "conda env list | grep three2six36 | rev | cut -d \" \" -f1 | rev")
PYENV27 := $(shell bash -c "conda env list | grep three2six27 | rev | cut -d \" \" -f1 | rev")
PYTHON36 := $(PYENV36)/bin/python
PYTHON27 := $(PYENV27)/bin/python

.setup_conda_envs.make_marker:
	conda create --name three2six36 python=3.6 --yes
	conda create --name three2six35 python=3.5 --yes
	conda create --name three2six34 python=3.4 --yes
	conda create --name three2six27 python=2.7 --yes
	touch .setup_conda_envs.make_marker

.install_all.make_marker: setup.py
	$(PYTHON36) -m scripts.install_in_all_envs
	touch .install_all.make_marker

.dev_install.make_marker: setup.py
	$(PYTHON36) -m pip install --upgrade --quiet \
		wheel twine \
		flake8 mypy pytest pytest-coverage rst2html5 \
		ipython pudb \
		astor;
	touch .dev_install.make_marker

setup_conda_envs: .setup_conda_envs.make_marker

install_all: .install_all.make_marker

dev_install: .dev_install.make_marker

clean:
	rm -f .setup_conda_envs.make_marker
	rm -f .install_all.make_marker
	rm -f .dev_install.make_marker

lint: .dev_install.make_marker
	MYPYPATH=$(PYENV36)/lib/python3.6/site-packages/:stubs/ \
	$(PYTHON36) -m mypy \
		--follow-imports=silent \
		--custom-typeshed-dir=/mnt/c/Users/mbark/typeshed \
		src/three2six/
	$(PYTHON36) -m flake8 src/three2six/

README.html: .dev_install.make_marker README.rst
	$(PYENV36)/bin/rst2html5 README.rst > README.html.tmp
	mv README.html.tmp README.html

debug_test: .dev_install.make_marker
	PYTHONPATH=src/:$$PYTHONPATH \
		$(PYTHON36) -m pytest -vv \
		--exitfirst \
		--capture=no tests/

test: .dev_install.make_marker README.html
	PYTHONPATH=src/:$$PYTHONPATH \
		$(PYTHON36) -m pytest tests/
	$(PYTHON36) -m pip uninstall three2six --quiet --yes
	$(PYTHON36) -m pip install . --force
	bash -c "cd test_project;$(PYTHON36) setup.py bdist_wheel --python-tag=py2.py3"
	$(PYTHON27) -m pip install --ignore-installed --quiet --force \
		test_project/dist/test_module-0.1.0-py2.py3-none-any.whl
	$(PYTHON27) -c "import test_module"
	# $(PYTHON36) -m pytest tests/

build: .dev_install.make_marker README.html
	$(PYTHON36) setup.py bdist_wheel upload

