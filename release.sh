# Clear any existing builds.
rm -rf ./dist

# Create a venv if not already there.
python3 -m venv .

# Activate the venv.
chmod +x ./bin/activate
source ./bin/activate

# Install dependencies.
python3 -m pip install --upgrade -r release_requirements.txt

# Build the release.
python3 -m build

# Release to PyPi.
# python3 -m twine upload --repository pypi dist/*
python3 -m twine upload dist/*

# Install the package from testPyPi.
# python3 -m pip install --index-url https://test.pypi.org/simple/ --no-deps amonite-mathorga

# Deactivate the venv.
deactivate