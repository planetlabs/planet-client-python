# Copyright 2015 Planet Labs, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from codecs import open as codecs_open
from setuptools import setup, find_packages


# Get the long description from the relevant file
try:
    with codecs_open('README.rst', encoding='utf-8') as f:
        long_description = f.read()
except:
    # @todo for now, fall back to this - pex fails to resolve the README
    long_description = ''


with open('planet/api/__version__.py') as f:
    for line in f:
        if line.find("__version__") >= 0:
            version = line.split("=")[1].strip()
            version = version.strip('"')
            version = version.strip("'")
            continue


test_requires = [
    'mock',
    'pytest',
    'requests-mock',
]

dev_requires = [
    'flake8',
    'setuptools',
    'pex',
    'pytest-cov',
    'sphinx',
    'wheel',
    'mock',
    'requests-mock',
]

setup(name='planet',
      version=version,
      description=u"Planet API Client",
      long_description=long_description,
      classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Scientific/Engineering',
        'Topic :: Software Development',
        'Topic :: Utilities'
      ],
      keywords='planet api client',
      author=u"Ian Schneider",
      author_email='ischneider@planet.com',
      url='https://github.com/planetlabs/planet-client-python',
      license='Apache 2.0',
      packages=find_packages(exclude=['examples', 'tests']),
      data_files=[('', ['LICENSE'])],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'click',
          'requests',
          'requests_futures == 0.9.7',
          'pywin32 >= 1.0;platform_system=="Windows"'
      ],
      extras_require={
          'test': test_requires,
          'dev': test_requires + dev_requires,
      },
      entry_points="""
      [console_scripts]
      planet=planet.scripts:main
      """
      )
