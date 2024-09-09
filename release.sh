# Clear any existing builds.
rm -rf ./dist

# Install or upgrade build.
python3 -m pip install --upgrade build
# Build the release.
python3 -m build

# Install or upgrade twine.
python3 -m pip install --upgrade twine
# Release to PyPi.
# python3 -m twine upload --repository pypi dist/*
python3 -m twine upload dist/*

# Install the package from testPyPi.
# python3 -m pip install --index-url https://test.pypi.org/simple/ --no-deps amonite-mathorga