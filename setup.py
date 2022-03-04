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
from pathlib import Path
from setuptools import setup, find_packages


with open('planet/__version__.py') as f:
    for line in f:
        if line.find("__version__") >= 0:
            version = line.split("=")[1].strip()
            version = version.strip('"')
            version = version.strip("'")
            continue


install_requires = [
    'click>=8.0.0',
    'httpx==0.16.1',
    'shapely>=1.7.1',
    'pyjwt>=2.1',
    'tqdm>=4.56',
]

test_requires = [
    'pytest',
    'pytest-asyncio==0.16',
    'pytest-cov',
    'respx==0.16.3'
]

lint_requires = [
    'flake8',
    'yapf'
]

doc_requires = [
    'mkdocs==1.1',
    'mkdocs-click==0.4.0',
    'mkdocs-material',
    'mkdocstrings==0.15.0'
]

setup(name='planet',
      version=version,
      description=u"Planet SDK for Python",
      long_description=Path("README.md").read_text("utf-8"),
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
      keywords='planet api sdk client',
      author='Jennifer Reiber Kyle',
      author_email='jennifer.kyle@planet.com',
      url='https://github.com/planetlabs/planet-client-python',
      license='Apache 2.0',
      packages=find_packages(exclude=['examples', 'tests']),
      data_files=[('', ['LICENSE'])],
      include_package_data=True,
      zip_safe=False,
      python_requires='>=3.7',
      install_requires=install_requires,
      extras_require={
          'test': test_requires,
          'lint': lint_requires,
          'docs': doc_requires,
          'dev': test_requires + lint_requires + doc_requires},
      entry_points={
          'console_scripts': [
              'planet=planet.cli.cli:main',
          ],
        },
      )
