from __future__ import print_function, absolute_import

import os
from setuptools import setup, find_packages

DESCRIPTION = "Python wrapper for Digital Ocean API v2"
VERSION = "0.3.0"

def write_version_py(filename=None):
    cnt = """\
version = '%s'
"""
    if not filename:
        filename = os.path.join(
            os.path.dirname(__file__), 'poseidon', 'version.py')

    a = open(filename, 'w')
    try:
        print(VERSION)
        a.write(cnt % (VERSION,))
    finally:
        a.close()

write_version_py()

setup(
    name='poseidon',
    version=VERSION,
    author='Chang She',
    packages = find_packages(),
    url='https://github.com/changhiskhan/poseidon',
    license='MIT',
    description=DESCRIPTION,
    package_data={'': ['requirements.txt']},
    install_requires = [
        'requests'
    ],
)
