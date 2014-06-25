# -*- coding: utf-8 -*-

from distutils.core import setup

setup(
    name='iktomi',
    version='0.4',
    packages=['iktomi',
              'iktomi.utils',
              'iktomi.forms',
              'iktomi.web',
              'iktomi.templates',
                    'iktomi.templates.mint', 'iktomi.templates.jinja2',
              'iktomi.db',
                    'iktomi.db.sqla',
              'iktomi.cli',
              'iktomi.unstable',
                    'iktomi.unstable.forms', 'iktomi.unstable.web',
                    'iktomi.unstable.utils',
                    'iktomi.unstable.db',
                        'iktomi.unstable.db.sqla'],
    package_dir={
        'iktomi.templates.jinja2': 'iktomi/templates/jinja2',
        'iktomi.templates.mint': 'iktomi/templates/mint',
    },
    package_data={
        'iktomi.templates.jinja2': ['templates/*/*.html'],
        'iktomi.templates.mint': ['templates/*/*.mint'],
    },
    requires=[
        'webob (>1.1b1)',
    ],
    author='Denis Otkidach',
    author_email='denis.otkidach@gmail.com',
    maintainer='Harut Dagesyan',
    maintainer_email='yes@harutune.name',
    description='A web tool: routing, forms, other useful things.',
    #long_description=open('README').read(),
    url='http://github.com/SmartTeleMax/iktomi/',
    license='MIT',
    keywords='web forms',
)
