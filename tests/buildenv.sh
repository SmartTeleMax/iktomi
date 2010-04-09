#!/bin/sh
echo Creating venv environment
virtualenv --no-site-packages venv

echo Install PIP inside virtual environment
./venv/bin/easy_install pip

echo Install insanities inside virtual environment
cd ..
./tests/venv/bin/python setup.py develop
cd ./tests/

echo Installing dependencies to venv environment
./venv/bin/pip install -E venv -r ./pipreq.txt
