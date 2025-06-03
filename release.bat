REM Clear any existing builds.
DEL /F /Q .\dist

REM Create a venv if not already there.
py -m venv .

REM Activate the venv.
CALL .\Scripts\activate.bat

REM Install or upgrade packages.
py -m pip install --upgrade -r release_requirements.txt

REM Build the release.
py -m build

REM Release to PyPi.
REM python3 -m twine upload --repository pypi dist/*
py -m twine upload dist\*

REM Install the package from testPyPi.
REM python3 -m pip install --index-url https://test.pypi.org/simple/ --no-deps amonite-mathorga

REM Deactivate the venv.
deactivate