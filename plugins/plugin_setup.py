#!/usr/bin/env python3
"""
Plugin setup helper script using uv package manager.
Automates virtual environment creation and dependency installation for plugins.
"""

import subprocess
import sys
import os
from pathlib import Path
import argparse


def run_command(cmd, cwd=None):
    """Run a command and handle errors."""
    try:
        result = subprocess.run(cmd, shell=True, cwd=cwd, check=True,
                              capture_output=True, text=True)
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {cmd}")
        print(f"Error output: {e.stderr}")
        return False


def get_python_path():
    """Get the correct Python interpreter path for the current environment."""
    # In Docker containers, Python is typically at /usr/local/bin/python
    # Fall back to sys.executable if the standard path doesn't exist
    standard_paths = ["/usr/local/bin/python", "/usr/bin/python3", "/usr/bin/python"]

    for path in standard_paths:
        if os.path.exists(path):
            return path

    # Fallback to current Python executable
    return sys.executable


def setup_plugin(plugin_name: str, force: bool = False):
    """Set up a plugin's virtual environment and dependencies."""
    plugin_dir = Path("plugins") / plugin_name

    if not plugin_dir.exists():
        print(f"Plugin directory {plugin_dir} does not exist.")
        return False

    venv_dir = plugin_dir / ".venv"

    # Check if venv already exists
    if venv_dir.exists() and not force:
        print(f"Virtual environment already exists for {plugin_name}. Use --force to recreate.")
        return False

    # Remove existing venv if force is True
    if venv_dir.exists() and force:
        print(f"Removing existing virtual environment for {plugin_name}...")
        import shutil
        shutil.rmtree(venv_dir)

    print(f"Setting up virtual environment for plugin: {plugin_name}")

    # Create virtual environment using uv
    python_path = get_python_path()
    if not run_command(f"uv venv .venv --python {python_path}", cwd=plugin_dir):
        return False

    # Install dependencies
    requirements_file = plugin_dir / "requirements.txt"
    pyproject_file = plugin_dir / "pyproject.toml"

    if pyproject_file.exists():
        print(f"Installing dependencies from pyproject.toml...")
        if not run_command(f"uv sync", cwd=plugin_dir):
            return False
    elif requirements_file.exists():
        print(f"Installing dependencies from requirements.txt...")
        if not run_command(f"uv pip install -r requirements.txt", cwd=plugin_dir):
            return False
    else:
        print(f"No requirements.txt or pyproject.toml found. Skipping dependency installation.")

    print(f"✅ Plugin {plugin_name} setup complete!")
    return True


def build_all_plugins(force: bool = False):
    """Build all plugins by setting up their virtual environments."""
    plugins_dir = Path("plugins")
    if not plugins_dir.exists():
        print("Plugins directory does not exist.")
        return False

    plugins_found = []
    for item in plugins_dir.iterdir():
        if item.is_dir() and not item.name.startswith("__"):
            plugins_found.append(item.name)

    if not plugins_found:
        print("No plugins found.")
        return True

    print(f"Found {len(plugins_found)} plugin(s): {', '.join(plugins_found)}")
    print("Building all plugins...\n")

    success_count = 0
    for plugin_name in plugins_found:
        print(f"--- Building plugin: {plugin_name} ---")
        if setup_plugin(plugin_name, force):
            success_count += 1
        print()  # Add spacing between plugins

    print(f"Build complete: {success_count}/{len(plugins_found)} plugins successfully built.")
    return success_count == len(plugins_found)


def list_plugins():
    """List all available plugins."""
    plugins_dir = Path("plugins")
    if not plugins_dir.exists():
        print("Plugins directory does not exist.")
        return

    print("Available plugins:")
    for item in plugins_dir.iterdir():
        if item.is_dir() and not item.name.startswith("__"):
            has_venv = (item / ".venv").exists()
            status = "✅" if has_venv else "❌"
            print(f"  {status} {item.name}")


def main():
    parser = argparse.ArgumentParser(description="Plugin setup helper using uv")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Setup command
    setup_parser = subparsers.add_parser("setup", help="Set up a plugin")
    setup_parser.add_argument("plugin_name", help="Name of the plugin to set up")
    setup_parser.add_argument("--force", action="store_true",
                             help="Force recreation of existing virtual environment")

    # Build command
    build_parser = subparsers.add_parser("build", help="Build all plugins")
    build_parser.add_argument("--force", action="store_true",
                             help="Force recreation of existing virtual environments")

    # List command
    subparsers.add_parser("list", help="List all plugins and their setup status")



    args = parser.parse_args()

    if args.command == "setup":
        success = setup_plugin(args.plugin_name, args.force)
        sys.exit(0 if success else 1)
    elif args.command == "build":
        success = build_all_plugins(args.force)
        sys.exit(0 if success else 1)
    elif args.command == "list":
        list_plugins()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()