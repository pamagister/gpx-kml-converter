<!-- This README.md is auto-generated from docs/index.md -->

# Welcome to python-template-project

A feature-rich Python project template with with auto-generated CLI, GUI and parameterized configuration.

[![Github CI Status](https://github.com/pamagister/python-template-project/actions/workflows/main.yml/badge.svg)](https://github.com/pamagister/python-template-project/actions)
[![GitHub release](https://img.shields.io/github/v/release/pamagister/python-template-project)](https://github.com/pamagister/python-template-project/releases)
[![Read the Docs](https://readthedocs.org/projects/python-template-project/badge/?version=stable)](https://python-template-project.readthedocs.io/en/stable/)
[![License](https://img.shields.io/github/license/pamagister/python-template-project)](https://github.com/pamagister/python-template-project/blob/main/LICENSE)
[![GitHub issues](https://img.shields.io/github/issues/pamagister/python-template-project)](https://github.com/pamagister/python-template-project/issues)
[![PyPI](https://img.shields.io/pypi/v/python-template-project)](https://pypi.org/project/python-template-project/)


This template provides a solid foundation for your next Python project, incorporating best practices for testing, automation, and distribution. It streamlines the development process with a comprehensive set of pre-configured tools and workflows, allowing you to focus on writing code.

## Installation

Download from [PyPI](https://pypi.org/).

💾 For more installation options see [install](docs/getting-started/install.md).

```bash
pip install python-template-project
```

Run GUI from command line

```bash
python-template-project-gui
```

## How to use this template

🐍 For details, see the [Getting Started](docs/develop/01_getting_started_dev.md) guide.


## Feature overview

* 📦 **Package Management:** Utilizes [uv](https://docs.astral.sh/uv/getting-started/), an extremely fast Python package manager, with dependencies managed in `pyproject.toml`.
* ✅ **Code Formatting and Linting:** Pre-commit hook with the [RUFF auto-formatter](https://docs.astral.sh/ruff/) to ensure consistent code style.
* 🧪 **Testing:** Unit testing framework with [pytest](https://docs.pytest.org/en/latest/).
* 📊 **Code coverage reports** using [codecov](https://about.codecov.io/sign-up/)
* 🔄 **CI/CD:**  [GitHub Actions](https://github.com/features/actions) for automated builds (Windows, macOS), unit tests, and code checks.
* 💾 **Automated Builds:** GitHub pipeline for automatically building a Windows executable and a macOS installer.
* 💬 **Parameter-Driven Automation:**
    * Automatic generation of a configuration file from parameter definitions.
    * Automatic generation of a Command-Line Interface (CLI) from the same parameters.
    * Automatic generation of CLI API documentation.
    * Automatic generation of change log using **gitchangelog** to keep a HISTORY.md file up to date.
* 📃 **Documentation:** Configuration for publishing documentation on [Read the Docs](https://about.readthedocs.com/) using [mkdocs](https://www.mkdocs.org/) .
* 🖼️ **Minimalist GUI:** Comes with a basic GUI based on [tkinker](https://tkdocs.com/tutorial/index.html) that includes an auto-generated settings menu based on your defined parameters.
* 🖥️ **Workflow Automation:** A `Makefile` is included to simplify and automate common development tasks.
* 🛳️ **Release pipeline:** Automated releases unsing the Makefile `make release` command, which creates a new tag and pushes it to the remote repo. The `release` pipeline will automatically create a new release on GitHub and trigger a release on  [PyPI](https://pypi.org.
    * **[setuptools](https://pypi.org/project/setuptools/)** is used to package the project and manage dependencies.
    * **[setuptools-scm](https://pypi.org/project/setuptools-scm/)** is used to automatically generate the `_version.py` file from the `pyproject.toml` file.

