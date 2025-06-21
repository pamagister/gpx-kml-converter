#!/usr/bin/env python3
"""
Unified entry point for CLI and GUI application.
Automatically detects whether to run CLI or GUI based on how the application is started.
"""

import os
import sys


def is_console_attached():
    """
    Check if the application is running in a console environment.
    Returns True if launched from console, False if launched via double-click.
    """
    try:
        # On Windows, check if we have a console attached
        if os.name == "nt":
            import ctypes

            kernel32 = ctypes.windll.kernel32
            # GetConsoleWindow returns 0 if no console is attached
            console_window = kernel32.GetConsoleWindow()
            if console_window == 0:
                return False

            # Check if the console was created by this process
            # (indicates double-click launch with console auto-created)
            process_list = kernel32.GetConsoleProcessList(None, 0)
            if process_list <= 1:
                return False

            return True
        else:
            # On Unix-like systems (macOS, Linux), check multiple indicators
            # Check if stdout is a terminal
            if not sys.stdout.isatty():
                return False

            # Additional check for macOS: Check if we're running in a .app bundle
            if sys.platform == "darwin":
                # If we're in a .app bundle, we're likely launched via double-click
                executable_path = sys.executable
                if ".app/" in executable_path:
                    # We're in an app bundle, check if we have a real terminal
                    # by checking if TERM environment variable is set
                    return os.environ.get("TERM") is not None

            return True
    except Exception as ex:
        # Fallback: assume GUI if we can't determine
        print(ex)
        return False


def has_command_line_args():
    """Check if command line arguments (beyond script name) are provided."""
    return len(sys.argv) > 1


def main():
    """Main entry point that decides between CLI and GUI."""

    # Force CLI mode if command line arguments are provided
    if has_command_line_args():
        run_cli()
        return

    # Check if we're in a console environment
    if is_console_attached():
        # We're in a console - offer choice or default to CLI
        print("Python Template Project")
        print("=" * 50)
        print("Detected console environment.")
        print("Options:")
        print("  1. Run CLI interface (default)")
        print("  2. Run GUI interface")
        print("  3. Show help")
        print()

        try:
            choice = input("Select option [1]: ").strip()
            if choice == "2":
                run_gui()
            elif choice == "3":
                show_help()
            else:
                run_cli()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting...")
            sys.exit(0)
    else:
        # Launched via double-click - start GUI
        run_gui()


def run_cli():
    """Launch the CLI interface."""
    try:
        from python_template_project.cli.cli import main as cli_main

        cli_main()
    except ImportError as e:
        print(f"Error importing CLI module: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error running CLI: {e}")
        sys.exit(1)


def run_gui():
    """Launch the GUI interface."""
    try:
        from python_template_project.gui.gui import main as gui_main

        gui_main()
    except ImportError as e:
        print(f"Error importing GUI module: {e}")
        # If GUI fails, fallback to CLI
        print("Falling back to CLI interface...")
        run_cli()
    except Exception as e:
        print(f"Error running GUI: {e}")
        print("Falling back to CLI interface...")
        run_cli()


def show_help():
    """Show help information."""
    print("""
Unified Application

Usage:
  When launched from console:
    - Without arguments: Interactive mode selection
    - With arguments: Direct CLI mode

  When launched via double-click:
    - Automatically starts GUI interface

Command Line Arguments:
  Run with any CLI arguments to force CLI mode.

Examples:
  python main.py --help          # Shows CLI help
  python main.py                 # Interactive mode selection
  double-click main.exe          # Starts GUI

""")


if __name__ == "__main__":
    main()
