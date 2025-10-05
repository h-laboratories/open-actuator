#!/usr/bin/env python3
"""
Script to help with PyPI publishing process.

This script automates the common steps for publishing to PyPI.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def run_command(command: str, check: bool = True) -> subprocess.CompletedProcess:
    """Run a shell command and return the result."""
    print(f"Running: {command}")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    
    if check and result.returncode != 0:
        print(f"Error running command: {command}")
        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")
        sys.exit(1)
    
    return result


def clean_build():
    """Clean build artifacts."""
    print("Cleaning build artifacts...")
    dirs_to_clean = ['build', 'dist', '*.egg-info']
    for pattern in dirs_to_clean:
        for path in Path('.').glob(pattern):
            if path.is_dir():
                shutil.rmtree(path)
                print(f"Removed {path}")


def build_package():
    """Build the package."""
    print("Building package...")
    run_command("python -m build")


def check_package():
    """Check the package."""
    print("Checking package...")
    run_command("twine check dist/*")


def upload_to_testpypi():
    """Upload to TestPyPI."""
    print("Uploading to TestPyPI...")
    run_command("twine upload --repository testpypi dist/*")


def upload_to_pypi():
    """Upload to PyPI."""
    print("Uploading to PyPI...")
    run_command("twine upload dist/*")


def install_from_testpypi():
    """Install package from TestPyPI for testing."""
    print("Installing from TestPyPI...")
    run_command("pip install --index-url https://test.pypi.org/simple/ open-actuator")


def install_from_pypi():
    """Install package from PyPI for testing."""
    print("Installing from PyPI...")
    run_command("pip install open-actuator")


def test_installation():
    """Test the installation."""
    print("Testing installation...")
    result = run_command("open-actuator-gui --help", check=False)
    if result.returncode == 0:
        print("✅ Installation test passed!")
    else:
        print("❌ Installation test failed!")
        print(result.stderr)


def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python scripts/publish.py <command>")
        print("Commands:")
        print("  clean       - Clean build artifacts")
        print("  build       - Build the package")
        print("  check       - Check the package")
        print("  testpypi    - Upload to TestPyPI")
        print("  pypi        - Upload to PyPI")
        print("  test        - Test installation from TestPyPI")
        print("  test-pypi   - Test installation from PyPI")
        print("  full-test   - Full test (build, check, upload to TestPyPI, test)")
        print("  full-pypi   - Full PyPI publish (build, check, upload to PyPI, test)")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "clean":
        clean_build()
    elif command == "build":
        clean_build()
        build_package()
    elif command == "check":
        check_package()
    elif command == "testpypi":
        upload_to_testpypi()
    elif command == "pypi":
        upload_to_pypi()
    elif command == "test":
        install_from_testpypi()
        test_installation()
    elif command == "test-pypi":
        install_from_pypi()
        test_installation()
    elif command == "full-test":
        clean_build()
        build_package()
        check_package()
        upload_to_testpypi()
        install_from_testpypi()
        test_installation()
    elif command == "full-pypi":
        clean_build()
        build_package()
        check_package()
        upload_to_pypi()
        install_from_pypi()
        test_installation()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
