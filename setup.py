#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@date: 2016-04-14

@author: Devin
"""
import os
import sys

import shutil

VERSION = "1.0.1"

if sys.argv[-1] == 'publish':
    if os.system("wheel version"):
        print("wheel not installed.\nUse `pip install wheel`.\nExiting.")
        sys.exit()
    if os.system("pip freeze | grep twine"):
        print("twine not installed.\nUse `pip install twine`.\nExiting.")
        sys.exit()
    os.system("python setup.py sdist bdist_wheel")
    os.system("twine upload -r pypi dist/*")
    print("You probably want to also tag the version now:")
    print("  git tag -a %s -m 'version %s'" % (VERSION, VERSION))
    print("  git push --tags")
    shutil.rmtree('dist')
    shutil.rmtree('build')
    shutil.rmtree('django_rest_schemas.egg-info')
    sys.exit()

elif sys.argv[-1] == "build":
    shutil.rmtree('dist')
    shutil.rmtree('build')
    shutil.rmtree('django_rest_schemas.egg-info')


from setuptools import setup, find_packages
setup(name='django_rest_schemas',
    version=VERSION,
    packages = find_packages(),
    description='for detail control of coreapi by django_rest_framework',
    author='Devin',
    author_email='waipbmtd@gmail.com',
    url='https://github.com/waipbmtd/django-rest-swagger-schemas',
    license='GPL',
    install_requires=[
        'coreapi',
        'openapi-codec',
        'simplejson'
      ],
    )