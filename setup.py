#!/usr/bin/env python
#
# (C) Copyright IBM Corp. 2020
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from setuptools import setup, find_packages

# how to get version info into the project
setup(
    name='cloudbutton',
    version='0.1.0',
    url='https://github.com/cloudbutton/cloudbutton',
    author='Cloudbutton Team',
    description='Run many jobs over the Cloud',
    long_description="Cloudbutton toolkit lets you transparently run your Python functions on any Cloud",
    author_email='cloudlab@urv.cat',
    packages=find_packages(),
    install_requires=[
        'pywren-ibm-cloud'
    ],
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.5',
)
