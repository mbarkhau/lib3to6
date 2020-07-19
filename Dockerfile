FROM registry.gitlab.com/mbarkhau/lib3to6/base

ADD src/ src/
ADD stubs/ stubs/
ADD test/ test/
ADD requirements/ requirements/
ADD test_project/ test_project/
ADD setup.cfg setup.cfg
ADD setup.py setup.py
ADD pylint-ignore.md pylint-ignore.md
ADD README.md README.md
ADD CHANGELOG.md CHANGELOG.md
ADD LICENSE LICENSE
ADD makefile makefile
ADD makefile.bootstrapit.make makefile.bootstrapit.make

ENV PYTHONPATH="src/:vendor/"

CMD make lint integration_test
