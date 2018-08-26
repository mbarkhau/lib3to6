import sys
import setuptools

packages = ["my_module"]
package_dir = {"": "."}

if any(arg.startswith("bdist") for arg in sys.argv):
    import lib3to6
    package_dir = lib3to6.fix(package_dir)

setuptools.setup(
    name="my-module",
    version="201808.1",
    packages=packages,
    package_dir=package_dir,
)
