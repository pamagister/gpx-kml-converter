import os
import argparse
import ast
import inspect

# Symbole
FOLDER_SYMBOL = "[D]"
FILE_SYMBOL = "[F]"
CLASS_SYMBOL = "[C]"
FUNC_SYMBOL = "[M]"
ATTR_SYMBOL = "[A]"
BRANCH = "|-- "
LAST_BRANCH = "`-- "
VERTICAL_LINE = "|   "
INDENT = "    "

# Ignorieren
IGNORE_DIRS = {
    ".pytest_cache",
    ".git",
    ".ruff",
    ".venv",
    ".github",
    "build",
    "dist",
    ".idea",
    "htmlcov",
    "__pycache__",
    "__main__",
    "site",
}
IGNORE_EXTENSIONS = {".pyc"}


def should_ignore(path):
    name = os.path.basename(path)
    if name in IGNORE_DIRS:
        return True
    if os.path.isfile(path):
        ext = os.path.splitext(path)[1]
        return ext in IGNORE_EXTENSIONS
    return False


def format_function_signature(func_node):
    """Erzeugt die Signatur einer Funktion als String"""
    args = []
    for arg in func_node.args.args:
        arg_str = arg.arg
        if arg.annotation:
            arg_str += f": {ast.unparse(arg.annotation)}"
        args.append(arg_str)
    if func_node.args.vararg:
        args.append(f"*{func_node.args.vararg.arg}")
    if func_node.args.kwarg:
        args.append(f"**{func_node.args.kwarg.arg}")
    args_str = ", ".join(args)
    ret = ""
    if func_node.returns:
        ret = f" -> {ast.unparse(func_node.returns)}"
    return f"{func_node.name}({args_str}){ret}"


def parse_python_file(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            node = ast.parse(f.read(), filename=file_path)
    except Exception:
        return []

    structure = []
    for child in node.body:
        if isinstance(child, ast.ClassDef):
            class_entry = {"type": "class", "name": child.name, "attributes": [], "methods": []}

            for item in child.body:
                if isinstance(item, ast.FunctionDef):
                    sig = format_function_signature(item)
                    class_entry["methods"].append(sig)
                elif isinstance(item, ast.Assign):
                    # Klassenattribute
                    for target in item.targets:
                        if isinstance(target, ast.Name):
                            class_entry["attributes"].append(target.id)
                elif isinstance(item, ast.AnnAssign):
                    if isinstance(item.target, ast.Name):
                        class_entry["attributes"].append(item.target.id)

                # Instanzattribute aus Methoden
                if isinstance(item, ast.FunctionDef):
                    for stmt in ast.walk(item):
                        if isinstance(stmt, ast.Assign):
                            for target in stmt.targets:
                                if (
                                    isinstance(target, ast.Attribute)
                                    and isinstance(target.value, ast.Name)
                                    and target.value.id == "self"
                                ):
                                    class_entry["attributes"].append(target.attr)
                        elif isinstance(stmt, ast.AnnAssign):
                            if (
                                isinstance(stmt.target, ast.Attribute)
                                and isinstance(stmt.target.value, ast.Name)
                                and stmt.target.value.id == "self"
                            ):
                                class_entry["attributes"].append(stmt.target.attr)

            structure.append(class_entry)

        elif isinstance(child, ast.FunctionDef):
            sig = format_function_signature(child)
            structure.append({"type": "function", "signature": sig})

    return structure


def show_tree(path, prefix="", show_code=False):
    try:
        items = sorted(os.listdir(path))
    except PermissionError:
        return

    items = [i for i in items if not should_ignore(os.path.join(path, i))]

    for index, item in enumerate(items):
        full_path = os.path.join(path, item)
        is_last = index == len(items) - 1
        connector = LAST_BRANCH if is_last else BRANCH
        symbol = FOLDER_SYMBOL if os.path.isdir(full_path) else FILE_SYMBOL

        print(f"{prefix}{connector}{symbol} {item}")
        next_prefix = prefix + (INDENT if is_last else VERTICAL_LINE)

        if os.path.isdir(full_path):
            show_tree(full_path, next_prefix, show_code)
        elif show_code and item.endswith(".py"):
            code_structure = parse_python_file(full_path)
            for entry in code_structure:
                if entry["type"] == "class":
                    # Attribute
                    attr_str = ', '.join(entry["attributes"]) if entry["attributes"] else "None"

                    print(f"{next_prefix}{BRANCH}{CLASS_SYMBOL} {entry['name']} - {ATTR_SYMBOL}: {attr_str}")
                    sub_prefix = next_prefix + VERTICAL_LINE

                    # Methoden mit Signatur
                    for method in entry["methods"]:
                        print(f"{sub_prefix}{BRANCH}{FUNC_SYMBOL} {entry['name']}.{method}")

                elif entry["type"] == "function":
                    print(f"{next_prefix}{BRANCH}{FUNC_SYMBOL} {entry['signature']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Shows directory and Python code structure as a tree."
    )
    parser.add_argument("path", nargs="?", default=".", help="Start directory")
    parser.add_argument(
        "--show-code",
        action="store_true",
        default=True,
        help="Shows functions, classes and attributes in .py files",
    )
    args = parser.parse_args()

    show_tree(args.path, show_code=args.show_code)

    print('\nSymbol description:')
    print(f"{FOLDER_SYMBOL} - Directory")
    print(f"{FILE_SYMBOL} - File")
    print(f"{CLASS_SYMBOL} - Class")
    print(f"{FUNC_SYMBOL} - Function/Method")
    print(f"{ATTR_SYMBOL} - Attribute")

