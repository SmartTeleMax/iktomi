# -*- coding: utf-8 -*-

from distutils.core import setup

setup(
    name='iktomi.unstable',
    version='0.3',
    packages=['iktomi', 'iktomi.unstable', 'iktomi.unstable.forms',
              'iktomi.unstable.web'],
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
