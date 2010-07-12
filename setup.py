# -*- coding: utf-8 -*-

from distutils.core import setup

setup(
    name="insanities",
    version="0.2",
    packages=["insanities","insanities.utils","insanities.forms",
              "insanities.web","insanities.ext","insanities.ext.jinja2",
              "insanities.ext.debug"], # is last package ok?
    package_data={
        '':["templates/*/*.html"]
    },
    requires=[
        "webob",
        "simplejson",# json encode, decode tool
        "html5lib",
        "mage", # commands support
    ],
    author="Denis Otkidach",
    author_email="denis.otkidach@gmail.com",
    maintainer="Tim Perevezentsev",
    maintainer_email="riffm2005@gmail.com",
    description="A set of insanities of several geeks to show ourselves our coolness.",
    url="http://github.com/riffm/insanities-testing/",
    license="MIT",
    keywords="web forms",
)
