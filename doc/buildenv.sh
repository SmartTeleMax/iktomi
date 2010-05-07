#!/bin/sh
echo Creating venv environment
virtualenv --no-site-packages venv

echo Install PIP inside virtual environment
./venv/bin/easy_install pip

echo Installing dependencies to venv environment
./venv/bin/pip install -E venv -r ./pipreq.txt
