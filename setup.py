# -*- coding: utf-8 -*-

from distutils.core import setup

setup(
    name='insanities',
    version='0.3',
    packages=['insanities', 'insanities.utils', 'insanities.forms',
              'insanities.web', 'insanities.templates', 'insanities.templates.mint',
              'insanities.templates.jinja2'],
    package_dir={
        'insanities.templates.jinja2':'insanities/templates/jinja2',
        'insanities.templates.mint':'insanities/templates/mint',
    },
    package_data={
        'insanities.templates.jinja2':['templates/*/*.html'],
        'insanities.templates.mint':['templates/*/*.mint'],
    },
    requires=[
        'webob',
    ],
    author='Denis Otkidach',
    author_email='denis.otkidach@gmail.com',
    maintainer='Tim Perevezentsev',
    maintainer_email='riffm2005@gmail.com',
    description='A set of insanities of several geeks to show ourselves our coolness.',
    long_description=open('README').read(),
    url='http://github.com/riffm/insanities-testing/',
    license='MIT',
    keywords='web forms',
)
