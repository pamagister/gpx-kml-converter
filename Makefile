.ONESHELL:
SHELL := /bin/bash
PYTHONIOENCODING := utf-8

.PHONY: help
help:             ## Show the help.
	@echo "Usage: make <target>"
	@echo ""
	@echo "Targets:"
	@fgrep "##" Makefile | fgrep -v fgrep


.PHONY: show
show:             ## Show the current environment.
	@echo "Current environment:"
	uv venv info

.PHONY: install
install:          ## Install the project in dev mode.
	$(MAKE) lock
	$(MAKE) virtualenv
	uv pip install -e .[dev,docs]

.PHONY: lock
lock:           ## builds the uv.make lock file and syncs the packages
	uv lock

.PHONY: precommit
# install automatic pre-commit run locally:
# uv pip install pre-commit # --> is usually configured in pyproject.toml
# uv run pre-commit install # --> will setup .git\hooks\pre-commit if a .pre-commit-config.yaml exists
precommit: ## Format, test and check dependencies.
	$(MAKE) fmt
	$(MAKE) test
	$(MAKE) deptry

.PHONY: fmt
fmt:              ## Format code using black & isort.
	uv run ruff format src/
	uv run ruff format tests/
	uv run ruff check src/ --fix
	uv run ruff check tests/ --fix

.PHONY: lint
lint:             ## Run pep8, black, mypy linters.
	uv run ruff check src/
	uv run ruff check tests/
	uv run ruff format --check src/
	uv run ruff format --check tests/
#	uv run mypy --ignore-missing-imports src/

.PHONY: test
test: lint        ## Run tests and generate coverage report.
	uv run pytest -v --cov-config .coveragerc --cov=src -l --tb=short --maxfail=1 tests/
	uv run coverage xml
	uv run coverage html

# ==========================
#   PROJECT SETTINGS
# ==========================

# Projektname
NAME := gpx-kml-converter

# Version automatisch aus git extrahieren
VERSION := $(shell git describe --tags --abbrev=0 2>/dev/null || echo "0.0.0")

# Release-Verzeichnis
RELEASE_DIR := release
DIST_DIR := dist

# Gemeinsame PyInstaller-Optionen
COMMON_PYI_OPTS = \
	--add-data "config.yaml:." \
    --hidden-import=PIL._tkinter_finder \
    --hidden-import=PIL.ImageTk \
    --collect-all=geopandas \
    --collect-all=shapely \
    --collect-all=pyogrio \
    --collect-all=PIL \
    --collect-submodules=PIL \
	--exclude-module pkg_resources \
    --exclude-module setuptools \

# ==========================
#   UTILS
# ==========================

.PHONY: prepare-release
prepare-release:
	rm -rf $(RELEASE_DIR)
	mkdir -p $(RELEASE_DIR)
	cp config.yaml $(RELEASE_DIR)/
	cp anniversaries.ini $(RELEASE_DIR)/
	cp locations_en.ini $(RELEASE_DIR)/
	cp locations_de.ini $(RELEASE_DIR)/
	cp README.md $(RELEASE_DIR)/
	cp -R res $(RELEASE_DIR)/
	cp -R docs $(RELEASE_DIR)/
	cp -R images $(RELEASE_DIR)/


# ==========================
#   WINDOWS BUILD
# ==========================

.PHONY: build-win
build-win: clean
	echo "Building Windows executable"
	uv run pyinstaller --onefile src/main.py \
		--name $(NAME) \
		$(COMMON_PYI_OPTS)

	$(MAKE) prepare-release
	cp $(DIST_DIR)/$(NAME).exe $(RELEASE_DIR)/



# ==========================
#   MACOS BUILD
# ==========================

.PHONY: build-macos
build-macos:
	echo "Building macOS CLI/GUI executable"
	uv run pyinstaller --onefile src/main.py \
		--name $(NAME) \
		$(COMMON_PYI_OPTS)

	echo "Building macOS .app bundle (GUI)"
	uv run pyinstaller --windowed src/main.py \
		--name "TemplateApp" \
		$(COMMON_PYI_OPTS)

	$(MAKE) prepare-release
	cp $(DIST_DIR)/$(NAME) $(RELEASE_DIR)/
	cp -R $(DIST_DIR)/TemplateApp.app $(RELEASE_DIR)/



# ==========================
#   LINUX BUILD
# ==========================

.PHONY: build-linux
build-linux: clean
	echo "Building Linux executable"
	uv run pyinstaller --onefile src/main.py \
		--name $(NAME) \
		$(COMMON_PYI_OPTS)

	$(MAKE) prepare-release
	cp $(DIST_DIR)/$(NAME) $(RELEASE_DIR)/


# ==========================
#   META TARGETS
# ==========================

.PHONY: build-all
build-all: build-win build-macos build-linux


.PHONY: watch
watch:            ## Run tests on every change.
	ls **/**.py | entr uv run pytest -s -vvv -l --tb=long --maxfail=1 tests/

.PHONY: clean
clean:            ## Clean unused files.
	@find ./ -name '*.pyc' -exec rm -f {} \;
	@find ./ -name '__pycache__' -exec rm -rf {} \;
	@find ./ -name 'Thumbs.db' -exec rm -f {} \;
	@find ./ -name '*~' -exec rm -f {} \;
	@rm -rf .cache
	@rm -rf .pytest_cache
	@rm -rf .mypy_cache
	@rm -rf build
	@rm -rf dist
	@rm -rf site
	@rm -rf *.egg-info
	@rm -rf htmlcov
	@rm -rf .tox/
	@rm -rf docs/_build

.PHONY: deptry
deptry:            ## Check for unused dependencies.
	uv pip install deptry
	uv run deptry src

.PHONY: virtualenv
virtualenv:       ## Create a virtual environment.
	uv venv

.PHONY: release
release:          ## Create a new tag for release.
	$(MAKE) precommit
	@echo "WARNING: This operation will create a version tag and push to GitHub"

	# Get the latest Git tag if it exists, otherwise default to 0.0.0 for calculations
	# 'git describe --tags --abbrev=0' gets the most recent tag
	# '|| echo 0.0.0' provides a fallback if no tags exist yet
	@CURRENT_TAG=$$(git describe --tags --abbrev=0 2>/dev/null || echo "0.0.0")
	@echo "Current (latest) Git tag: $$CURRENT_TAG"

	# Suggest next patch version based on the current tag
	IFS=. read -r MAJOR MINOR PATCH <<< "$$CURRENT_TAG"
	@NEXT_PATCH_VERSION="$$MAJOR.$$MINOR.$$((PATCH + 1))"

	# Prompt the user for the new tag, suggesting the next patch version by default
	read -e -i "$$NEXT_PATCH_VERSION" -p "Enter the new release tag (e.g., 1.0.0, 1.1.0, 1.1.1): " NEW_TAG

	# Generate changelog *before* tagging, based on existing history up to the new tag point
	uv run gitchangelog > HISTORY.md
	git add HISTORY.md
	git commit -m "docs: Update HISTORY.md for release $${NEW_TAG}"

	echo "Creating git tag : $${NEW_TAG}"
	git tag "$${NEW_TAG}"
	git push -u origin HEAD --tags

	echo "GitHub Actions will detect the new tag and trigger the release workflows."
	echo "Add modified files to commit and push them to main"

.PHONY: docs
docs:             ## Build and sync the documentation.
	@echo "sync documentation ..."
	@uv run ./scripts/generate_config_docs.py
	@uv run ./scripts/update_readme.py
	@uv run ./.github/update_funding.py
	@echo "building documentation ..."
	@uv run mkdocs build
	@uv run mkdocs serve

.PHONY: list
list:            ## Show project file list (excluding ignored folders)
	@powershell -NoProfile -ExecutionPolicy Bypass -File ./scripts/show_filelist.ps1

.PHONY: tree
tree:            ## Show project tree (excluding ignored folders)
	@powershell -NoProfile -ExecutionPolicy Bypass -File ./scripts/show_tree.ps1

.PHONY: pytree
pytree:            ## Show project tree (excluding ignored folders)
	@uv run ./scripts/show_tree.py

.PHONY: init
init:             ## Initialize the project based on an application template.
	@./.github/init.sh
