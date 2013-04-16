#!./venv/bin/python
from app import wsgi_app

from wsgiref.simple_server import make_server


if __name__ == '__main__':
    server = make_server('', 8000, wsgi_app)
    server.serve_forever()

