# Naming Conventions in Python Projects

In Python projects, it's crucial to use consistent naming conventions to ensure code readability and maintainability. The choice between underscores (`_`) and hyphens (`-`) largely depends on the context.

---

## Underscores (`_`) – Snake_case

Primarily use underscores **within your Python code** for multi-word names. This is known as `snake_case`.

* **Python Package Names (Internal):** The importable name of your Python package (e.g., the folder under `src/`) should use underscores.
    * **Example:** `src/my_python_package` is imported as `import my_python_package`.
* **Module Names (.py files):** Python file names that are modules should also use underscores.
    * **Example:** `my_module.py`, `data_processing.py`.
* **Variables, Functions, and Methods:** Within your code, these names should follow `snake_case`.
    * **Example:** `my_variable`, `calculate_total()`, `_private_function()`.

---

## Hyphens (`-`) – Kebab-case

Primarily use hyphens **outside of your Python code** for filesystem, URL, and human-readable names. This is often referred to as `kebab-case`.

* **PyPI Package Name (Project Name):** The name under which your project is published on PyPI and installed with `pip install` should use hyphens.
    * **Example:** In `pyproject.toml`: `name = "my-python-project"`. Installation: `pip install my-python-project`.
* **Main Project Folder / Repository Name:** The root folder of your project in the file system.
    * **Example:** `my-python-project/`.
* **Documentation Folders and Files (MkDocs, ReadTheDocs):** Folders and Markdown files within your documentation.
    * **Example:** `docs/getting-started/installation-guide.md`.
* **Command-Line Tools / Scripts:** Names for executable scripts you define in your `pyproject.toml` under `[project.scripts]`.
    * **Example:** `my-cli-tool = "my_python_package.cli:main"`.

---

## Summary of Recommendations

| Context                       | Recommended Convention | Example                          |
| :---------------------------- | :--------------------- |:---------------------------------|
| **Internal Python Name** | Underscores (`_`)      | `my_python_package`              |
| **PyPI / Project Name** | Hyphens (`-`)          | `my-python-package`              |
| **Module Filename** | Underscores (`_`)      | `my_module.py`                   |
| **Repository/Root Folder** | Hyphens (`-`)          | `my-python-project/`             |
| **Docs Folders/Files** | Hyphens (`-`)          | `getting-started/cli-usage.md`   |
| **CLI Commands** | Hyphens (`-`)          | `my-cli-tool`                    |

Consistently applying these rules significantly improves the clarity and professionalism of your Python project.