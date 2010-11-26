#!/bin/sh
echo Creating venv environment
virtualenv --no-site-packages venv

echo Install PIP inside virtual environment
./venv/bin/easy_install pip

echo Install insanities inside virtual environment
cd ../..
./examples/blogs/venv/bin/python setup.py develop
cd ./examples/blogs/

echo Installing dependencies to venv environment
./venv/bin/pip install -E venv -r ./pipreq.txt
