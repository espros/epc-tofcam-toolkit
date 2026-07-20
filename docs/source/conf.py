# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

from importlib.metadata import version
import sys
sys.path.insert(0, '../../src')
from epc_docs.common_conf import apply_common_config
from typing import cast

__version__ = version('epc-tofcam-toolkit')

apply_common_config(globals(), 'EPC TOFcam Toolkit', __version__)

# Tell static analyzers these names are injected by apply_common_config.
extensions = cast(list[str], globals().get("extensions", []))
html_static_path = cast(list[str], globals().get("html_static_path", []))
source_suffix = cast(dict[str, str], globals().get("source_suffix", {}))
project = cast(str, globals().get("project", ""))
epc_docs_url = cast(str, globals().get("epc_docs_url", ""))
myst_substitutions = cast(dict[str, str], globals().get("myst_substitutions", {}))
intersphinx_mapping = cast(dict[str, str], globals().get("intersphinx_mapping", {}))

extensions += ['myst_parser', 'sphinx.ext.autodoc', 'sphinx.ext.napoleon']

autodoc_mock_imports = ["matplotlib", "serial", "PIL"]

