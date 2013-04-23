# -*- coding: utf-8 -*-

from distutils.core import setup

setup(
    name='iktomi.unstable',
    version='0.3',
    packages=['iktomi.unstable'],
    # XXX isn't it needed? Or is it only for py3k?
    #namespace_packages=['iktomi'],
    #package_data={
    #},
    requires=[
        'webob (>1.1b1)',
        'iktomi (>0.3)',
    ],
    author='Denis Otkidach',
    author_email='denis.otkidach@gmail.com',
    maintainer='Tim Perevezentsev',
    maintainer_email='riffm2005@gmail.com',
    description='Unstable extensions for iktomi.',
    #long_description=open('README').read(),
    url='http://github.com/SmartTeleMax/iktomi-unstable/',
    license='MIT',
    #keywords='',
)
