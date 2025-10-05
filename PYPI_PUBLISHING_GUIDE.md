# PyPI Publishing Guide for Open Actuator

This guide explains how to publish the Open Actuator package to PyPI (Python Package Index).

## Prerequisites

1. **PyPI Account**: Create an account at [pypi.org](https://pypi.org)
2. **TestPyPI Account**: Create an account at [test.pypi.org](https://test.pypi.org) for testing
3. **API Token**: Generate an API token for authentication

## Step 1: Prepare Your Package

### 1.1 Update Package Information

Before publishing, make sure to update the following in `pyproject.toml`:

- **Version**: Update the version number for each release
- **Author Information**: Update email and name if needed
- **URLs**: Update repository URLs to point to your actual repository
- **Description**: Ensure the description is clear and informative

### 1.2 Test Your Package Locally

```bash
# Install build tools
pip install build twine

# Build the package
python -m build

# Check the package
twine check dist/*

# Test install from local build
pip install dist/open_actuator-0.1.0-py3-none-any.whl
```

## Step 2: Test on TestPyPI (Recommended)

### 2.1 Upload to TestPyPI

```bash
# Upload to TestPyPI
twine upload --repository testpypi dist/*

# Install from TestPyPI to test
pip install --index-url https://test.pypi.org/simple/ open-actuator
```

### 2.2 Test the Installation

```bash
# Test the command-line interface
open-actuator-gui --help

# Test the GUI (if you have a display)
open-actuator-gui
```

## Step 3: Publish to PyPI

### 3.1 Upload to PyPI

```bash
# Upload to PyPI
twine upload dist/*
```

### 3.2 Verify Installation

```bash
# Install from PyPI
pip install open-actuator

# Test the installation
open-actuator-gui --help
```

## Step 4: Automated Publishing with GitHub Actions

### 4.1 Set up GitHub Secrets

1. Go to your GitHub repository
2. Navigate to Settings → Secrets and variables → Actions
3. Add the following secrets:
   - `PYPI_API_TOKEN`: Your PyPI API token

### 4.2 Create a Release

1. Go to your GitHub repository
2. Click "Releases" → "Create a new release"
3. Create a new tag (e.g., `v0.1.0`)
4. Add release notes
5. Publish the release

The GitHub Action will automatically build and publish to PyPI.

## Step 5: Version Management

### 5.1 Semantic Versioning

Use semantic versioning (MAJOR.MINOR.PATCH):
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### 5.2 Update Version

Update the version in `pyproject.toml`:

```toml
[project]
version = "0.1.1"  # Update this for each release
```

## Step 6: Package Maintenance

### 6.1 Update Dependencies

Regularly update dependencies in `requirements.txt` and `pyproject.toml`.

### 6.2 Monitor Package Usage

- Check PyPI download statistics
- Monitor GitHub issues and pull requests
- Update documentation as needed

## Troubleshooting

### Common Issues

1. **Authentication Errors**:
   ```bash
   # Make sure you're using the correct API token
   twine upload --username __token__ --password <your-api-token> dist/*
   ```

2. **Package Already Exists**:
   - Update the version number in `pyproject.toml`
   - Rebuild the package

3. **Build Errors**:
   ```bash
   # Clean build artifacts
   rm -rf build/ dist/ *.egg-info/
   python -m build
   ```

4. **Import Errors**:
   - Check that all dependencies are listed in `pyproject.toml`
   - Test the package installation in a clean environment

### Testing Commands

```bash
# Test package building
python -m build

# Test package checking
twine check dist/*

# Test installation
pip install dist/open_actuator-*.whl

# Test uninstallation
pip uninstall open-actuator
```

## Best Practices

1. **Always test on TestPyPI first**
2. **Use semantic versioning**
3. **Keep dependencies up to date**
4. **Write comprehensive release notes**
5. **Monitor for issues after release**
6. **Use automated workflows for consistency**

## Security Considerations

1. **Never commit API tokens to version control**
2. **Use GitHub Secrets for CI/CD**
3. **Regularly rotate API tokens**
4. **Use 2FA on PyPI account**

## Useful Commands

```bash
# Build package
python -m build

# Check package
twine check dist/*

# Upload to TestPyPI
twine upload --repository testpypi dist/*

# Upload to PyPI
twine upload dist/*

# Install from PyPI
pip install open-actuator

# Install with development dependencies
pip install open-actuator[dev]

# Run tests
pytest

# Format code
black src/

# Lint code
flake8 src/
```

## Next Steps

After successful publishing:

1. **Update documentation** with installation instructions
2. **Create a GitHub release** with the same version
3. **Announce the release** in relevant communities
4. **Monitor for issues** and user feedback
5. **Plan the next release** based on feedback
