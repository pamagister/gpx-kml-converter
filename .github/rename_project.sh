#!/usr/bin/env bash

# Hilfsfunktion für Fehlermeldungen und Beenden
function die { echo "$*" >&2; exit 1; }

# parse args
while getopts a:p:n:d: flag
do
    case "${flag}" in
        a) author=${OPTARG};;
        p) package_name=${OPTARG};; # The new internal Python package name (snake_case)
        n) project_name=${OPTARG};; # The new external project name (kebab-case)
        d) description=${OPTARG};;
        *) die "Unknown Flag: $flag";;
    esac
done

# Check whether all required arguments have been passed
[[ -z "$author" ]] && die "Missing Argument: -a (author)"
[[ -z "$package_name" ]] && die "Missing Argument: -p (package_name)"
[[ -z "$project_name" ]] && die "Missing Argument: -n (project_name)"
[[ -z "$description" ]] && die "Missing Argument: -d (description)"

echo "Author: $author";
echo "New Python Package Name (internal): $package_name";
echo "New Project Name (external/PyPI): $project_name";
echo "Description: $description";

echo "Renaming project content..."

# Old identifiers
original_author="pamagister"
original_project_name="python-template-project"
original_package_name="python_template_project"
original_description="Feature-rich Python project template designed for robustness and ease of use."

# Customize all file contents first
# Use 'git ls-files' to edit only versioned files
# Note the order: Replace more specific with more specific first,
# then more general ones.
# Important: Escape special characters in the variables if they could occur in the replacements.
# Here the variables are relatively safe as they only contain alphanumeric characters and hyphens/underscores.

for filename in $(git ls-files)
do
    # Skip files in the .github/ directory
    if [[ "$filename" == ".github"* ]]; then
        echo "Skipping .github file: $filename"
        continue
    fi
    # Replace the old internal package name with the new internal package name
    sed -i "s/$original_package_name/$package_name/g" "$filename"
    # Replace the old external project name with the new external project name
    sed -i "s/$original_project_name/$project_name/g" "$filename"
    # Replace the old author
    sed -i "s/$original_author/$author/g" "$filename"
    # Replace the old description with the new one
    sed -i "s/$original_description/$description/g" "$filename"
    echo "Processed: $filename"
done

# Then rename the directory
# Check if the directory exists before renaming it
OLD_PACKAGE_DIR="src/$original_package_name"
NEW_PACKAGE_DIR="src/$package_name"

if [ -d "$OLD_PACKAGE_DIR" ]; then
    echo "Renaming directory: $OLD_PACKAGE_DIR to $NEW_PACKAGE_DIR"
    mv "$OLD_PACKAGE_DIR" "$NEW_PACKAGE_DIR"
else
    echo "Warning: Directory $OLD_PACKAGE_DIR not found. Skipping directory rename."
fi

# Remove the template.yml to indicate that the template has been applied
echo "Removing .github/template.yml"
rm -f .github/template.yml

echo "Project renaming complete!"