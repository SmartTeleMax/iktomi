#!./venv/bin/python
from app import app

from wsgiref.simple_server import make_server


if __name__ == '__main__':
    make_server('', '8000', app)

