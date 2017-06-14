# -*- coding: utf-8 -*-
import sys
from distutils.core import setup


install_requires = ['six']
extras_requires = {
    'web': ['webob'],
    'fcgi': ['flup6'],
    'sqla': ['sqlalchemy'],
    'memcached': ['python-memcached'],
    'cleanhtml': ['lxml'],
    'renderhtml': ['jinja2'],
    'images': ['pillow'],
}

tests_requires = [
    'pymysql',
    'testalchemy==0.4',
    'pytest',
    'pytest-cov',
    'mockcache==1.0.3_alpha',
    'webtest',
]
if sys.version_info[0] < 3:
    tests_requires.append('mock')

dependency_links = [
    'https://github.com/ods/testalchemy/tarball/master#egg=testalchemy-0.4',
    'https://github.com/lunant/mockcache/tarball/master#egg=mockcache-1.0.3_alpha',
]

extras_requires['tests'] = tests_requires

setup(
    name='iktomi',
    version='0.5.2',
    packages=['iktomi',
              'iktomi.utils',
              'iktomi.forms',
              'iktomi.web',
              'iktomi.templates',
                    'iktomi.templates.jinja2',
              'iktomi.db',
                    'iktomi.db.sqla',
              'iktomi.cli',
              'iktomi.unstable',
                    'iktomi.unstable.forms',
                    'iktomi.unstable.utils',
                    'iktomi.unstable.db',
                        'iktomi.unstable.db.sqla'],
    package_dir={
        'iktomi.templates.jinja2': 'iktomi/templates/jinja2',
    },
    package_data={
        'iktomi.templates.jinja2': ['templates/*/*.html'],
    },
    install_requires=install_requires,
    extras_require=extras_requires,
    tests_require=tests_requires,
    dependency_links=dependency_links,
    author='Denis Otkidach',
    author_email='denis.otkidach@gmail.com',
    maintainer='Harut Dagesyan',
    maintainer_email='yes@harutune.name',
    description='A web tool: routing, forms, other useful things.',
    # long_description=open('README').read(),
    url='http://github.com/SmartTeleMax/iktomi/',
    license='MIT',
    keywords='web forms',
)
