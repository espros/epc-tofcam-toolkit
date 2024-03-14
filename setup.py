from setuptools import setup

# Load the package's __version__.py module as a dictionary.
# we cannot include the package jet since it is not installed yet
version_ns = {}
with open('src/epc/_version.py') as f:
    exec(f.read(), version_ns)

setup(version=version_ns['__version__'])