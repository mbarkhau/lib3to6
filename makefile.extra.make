

## Start the development http server in debug mode
##    This is just to illustrate how to add your
##    extra targets outside of the main makefile.
.PHONY: serve
serve:
	echo "Not Implemented"


.PHONY: bump_version_old
bump_version_old:
	date +"v%Y%m." > .new_version.txt
	awk 'match($$0, /v[0-9]+.([0-9]+)(-[a-z]*)?/, arr) { printf "%04d%s\n", (arr[1]+1), arr[2] }' \
		version.txt >> .new_version.txt
	sed -i -z 's/\n//g' .new_version.txt
	cat version.txt >> old_versions.txt
	echo "" >> old_versions.txt
	mv .new_version.txt version.txt
	sed -i "s/__version__ = \".*\"/__version__ = \"$$(cat version.txt)\"/" setup.py
	sed -i "s/__version__ = \".*\"/__version__ = \"$$(cat version.txt)\"/" \
		src/lib3to6/__init__.py
	sed -i "s/CalVer-.*-blue.svg/CalVer-$$(cat version.txt | sed 's/-/--/')-blue.svg/" \
		README.rst
	sed -i "s/CalVer .*/CalVer $$(cat version.txt)/" README.rst


.PHONY: fulltest_old
fulltest_old:
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