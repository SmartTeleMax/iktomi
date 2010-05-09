# -*- coding: utf-8 -*-

import ez_setup
ez_setup.use_setuptools()

from setuptools import setup

setup(
    name="insanities",
    version="",
    packages=["insanities","insanities.utils","insanities.forms",
              "insanities.web","insanities.ext"],
    package_data={
        '':["templates/*/*.html"]
    },
    install_requires=[
        "jinja2",# template engine
        "demjson",# json encode, decode tool
        "webob",

        #XXX Soon to be gone
        #"sqlalchemy",
        "pytils",
        #"werkzeug",
    ],
    author="Denis Otkidach",
    author_email="denis.otkidach@gmail.com",
    description="A set of insanities of several geeks to show ourselves our coolness.",
    license="MIT",
    keywords="forms web",
)
