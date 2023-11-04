# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.abspath(".."))

# -- Project information -----------------------------------------------------

project = "svsfunc"

exec(Path(f"../{project}/_metadata.py").read_text(), meta := dict[str, str]())

copyright = f"{datetime.now().year}, {meta['__author_name__']}"
author = meta["__author__"]

# The short X.Y version
version = meta['__version__']

# The full version, including alpha/beta/rc tags
release = meta["__version__"]


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.todo",
    "sphinx_autodoc_typehints",
    "sphinx_toolbox.more_autodoc.typevars"
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "sphinx_rtd_theme"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
# stolen from vardautomation
html_static_path = ['_static']
html_css_files = ['css/theme_overrides.css']
html_style = 'css/theme_overrides.css'


# -- Extension configuration -------------------------------------------------

autosummary_generate = True
autodoc_default_options = {
    'members': True,
    'undoc-members': True,
    'member-order': 'bysource',
    'special-members': '__init__',
}
autodoc_typehints = "signature"
autodoc_mock_imports = [
    re.split("[>=~]=", line.strip())[0].lower() for line in Path("../requirements.txt").open()
] + ["vardautomation"]
pygments_style = 'sphinx'


# -- Options for todo extension ----------------------------------------------

# If true, `todo` and `todoList` produce output, else they produce nothing.
todo_include_todos = True
