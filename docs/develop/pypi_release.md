# Releasing Your Python Project to PyPI

This guide will walk you through the process of publishing your Python package to the Python Package Index (PyPI), making it available for others to install using `pip`.

## 1. Create a User Account on PyPI

Before you can publish, you need a PyPI account.

* Go to the [PyPI registration page](https://pypi.org/account/register/).
* Fill in the required information (username, email, password).
* **Important**: PyPI has a test instance called [TestPyPI](https://test.pypi.org/). It's highly recommended to perform your first few releases to TestPyPI to ensure everything works correctly without cluttering the main PyPI index. You'll need a separate account for TestPyPI.

## 2. Generate a PyPI API Token

Using an API token is the most secure way to authenticate with PyPI for automated deployments, as it avoids exposing your password.

* Log in to your PyPI account (either on `pypi.org` or `test.pypi.org`).
* Navigate to **Account settings**.
* Under the "API tokens" section, click "Add API token".
* Give the token a descriptive name (e.g., "GitHub Actions Release").
* For "Scope," select **"Entire account"** for initial setup. For more secure, fine-grained control, you can specify individual projects once they are created on PyPI.
* Click "Add token".
* **Crucially, copy the entire token string immediately.** You will not be able to see it again. Store it securely.

## 3. Configure Your Project for Packaging

Your Python project needs a `pyproject.toml` file (recommended for modern projects) or a `setup.py` file to define its metadata and how it should be packaged.

### Option A: `pyproject.toml` (Recommended Modern Approach)

Create a file named `pyproject.toml` in the root of your project.
In case of this template project, this file is already present, but you may need to adjust it according to your project specifics.

```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "your-package-name" # Must be unique on PyPI
version = "0.1.0" # This will be replaced by your tag version in CI/CD
authors = [
  { name="Your Name", email="your.email@example.com" },
]
description = "A short description of your project."
readme = "README.md"
requires-python = ">=3.8"
classifiers = [
    "Programming Language :: Python :: 3",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
]
dependencies = [
    # List your project's runtime dependencies here, ect.
    # "requests>=2.28.1",
    # "numpy",
]

[project.urls]
Homepage = "[https://github.com/your-username/your-repo](https://github.com/your-username/your-repo)"
"Bug Tracker" = "[https://github.com/your-username/your-repo/issues](https://github.com/your-username/your-repo/issues)"

# Optional: if you have scripts or entry points
# [project.scripts]
# your_command_name = "your_package.module:main_function"

# Optional: if you have a package directory structure
# [tool.setuptools.packages.find]
# where = ["src"] # if your code is in a `src` directory
# include = ["your_package_name*"]
````

**Key Points for `pyproject.toml`:**

  * **`name`**: This is the name your users will use to `pip install` your package. It **must be unique** on PyPI. Check `pypi.org/project/your-package-name/` to see if it's taken.
  * **`version`**: For CI/CD, this will typically be updated automatically from your Git tag. Keep it as `0.1.0` or similar for local testing.
  * **`readme`**: Ensure this points to your `README.md` file (or `README.rst` if you use reStructuredText).
  * **`dependencies`**: List all packages your project requires to run, including version specifiers (e.g., `requests>=2.28.1`).
  * **`classifiers`**: Help users find your project. Refer to the [list of PyPI classifiers](https://pypi.org/classifiers/).

### Option B: `setup.py` (Older, but still widely used)

Create a file named `setup.py` in the root of your project:

```python
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="your-package-name", # Must be unique on PyPI
    version="0.1.0", # This will be replaced by your tag version in CI/CD
    author="Your Name",
    author_email="your.email@example.com",
    description="A short description of your project.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="[https://github.com/your-username/your-repo](https://github.com/your-username/your-repo)",
    packages=find_packages(), # Automatically finds packages in your directory
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
    install_requires=[
        # List your project's runtime dependencies here
        # "requests>=2.28.1",
        # "numpy",
    ],
    # If you have scripts
    # entry_points={
    #     'console_scripts': [
    #         'your_command_name = your_package.module:main_function',
    #     ],
    # },
)
```

**Note:** If you use `setup.py`, ensure you have a `MANIFEST.in` file to include non-Python files like `config.yaml` or `README.md` in your distribution. For `pyproject.toml`, the `include` option in `[tool.setuptools.packages.find]` or `[tool.setuptools.package-data]` can handle this.

## 4\. Local Testing: Build and Upload to TestPyPI

Before pushing to GitHub, test your packaging locally.

1.  **Install build and twine:**

    ```bash
    pip install build twine
    ```

2.  **Build your distribution packages:**
    Navigate to your project's root directory (where `pyproject.toml` or `setup.py` is located) and run:

    ```bash
    python -m build
    ```

    This will create `*.whl` (wheel) and `*.tar.gz` (source distribution) files in a newly created `dist/` directory.

3.  **Upload to TestPyPI:**

    ```bash
    twine upload --repository testpypi dist/*
    ```

    You'll be prompted for your TestPyPI username (`__token__`) and the API token you generated for TestPyPI.

4.  **Verify the upload:**
    Go to `test.pypi.org/project/your-package-name/` and ensure your package is there and looks correct.

5.  **Test installation:**

    ```bash
    pip install --index-url [https://test.pypi.org/simple/](https://test.pypi.org/simple/) --no-deps your-package-name
    ```

    Replace `your-package-name` with the actual name from your `pyproject.toml`/`setup.py`.

## 5\. Configure GitHub Actions for Automated PyPI Release

You've already got a good start with your `release.yml`. Here's how to integrate the PyPI API token securely.

### 5.1. Add PyPI API Token as a GitHub Secret

1.  Go to your GitHub repository.
2.  Navigate to **Settings** \> **Secrets and variables** \> **Actions**.
3.  Click on **New repository secret**.
4.  For **Name**, enter `PYPI_API_TOKEN`.
5.  For **Secret**, paste the API token you copied from PyPI (the one for `pypi.org`, not `test.pypi.org`).
6.  Click **Add secret**.

### 5.2. Ensure `release.yml` is Correct

Your `deploy` job in `release.yml` should now look like the adjusted version provided at the beginning of this response.

```yaml
# ... (previous parts of your release.yml) ...

jobs:
  # ... (your existing 'release' job for GitHub Releases) ...

  deploy:
    needs: release # Ensures GitHub release is created first
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11' # Use a specific version, e.g., '3.9', '3.11'
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install build twine # Install 'build' for packaging and 'twine' for uploading
    - name: Build and publish
      env:
        # TWINE_USERNAME should always be '__token__' when using an API token
        TWINE_USERNAME: __token__
        # This references the secret you created in GitHub
        TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
      run: |
        python -m build # Builds your source and wheel distributions
        twine upload dist/* # Uploads all packages in the dist/ directory
```

## 6\. Triggering a Release

Once your `pyproject.toml` (or `setup.py`) is in place, and your GitHub Actions workflow is correctly configured with the `PYPI_API_TOKEN` secret:

  * **For a new release:** Create a new Git tag and push it to GitHub.

    ```bash
    git tag -a v0.1.0 -m "First PyPI release"
    git push origin v0.1.0
    ```

    This will trigger both your `build` workflow (if it's also on tags) and your `release.yml` workflow (`release` and `deploy` jobs).

  * **For manual trigger:** Go to the "Actions" tab in your GitHub repository, select your "Upload Python Package" workflow, and click "Run workflow".

## 7\. Verifying the PyPI Release

After the GitHub Actions workflow completes successfully:

  * Go to `pypi.org/project/your-package-name/`.
  * Verify that your package, description, version, and files are all correct.

Congratulations\! Your Python project is now officially available on PyPI.

```
```