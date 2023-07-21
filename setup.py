# Copyright 2015 Planet Labs, Inc.
# Copyright 2022 Planet Labs PBC.
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
    'click>=8.0',
    'geojson',
    'httpx>=0.23.0',
    'jsonschema',
    'pyjwt>=2.1',
    'tqdm>=4.56',
    'typing-extensions',
]

test_requires = ['pytest', 'anyio', 'pytest-cov', 'respx>=0.20']

lint_requires = ['flake8', 'mypy', 'yapf']

doc_requires = [
    'mkdocs==1.3',
    'mkdocs-click==0.7.0',
    'mkdocs-material==8.2.11',
    'mkdocstrings==0.18.1'
]

setup(
    name='planet',
    version=version,
    description=u"Planet SDK for Python",
    long_description=Path("README.md").read_text("utf-8"),
    long_description_content_type="text/markdown",
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Topic :: Scientific/Engineering',
        'Topic :: Software Development',
        'Topic :: Utilities'
    ],
    keywords='planet api sdk client',
    author='Jennifer Reiber Kyle',
    maintainer='Planet Dev Rel Team',
    maintainer_email='developers@planet.com',
    url='https://github.com/planetlabs/planet-client-python',
    license='Apache 2.0',
    packages=find_packages(exclude=['examples', 'tests']),
    package_data={
        "": ["LICENSE", "CONTRIBUTING.md"],
        "planet": ["data/*"],
    },
    include_package_data=True,
    zip_safe=False,
    python_requires='>=3.7',
    install_requires=install_requires,
    extras_require={
        'test': test_requires,
        'lint': lint_requires,
        'docs': doc_requires,
        'dev': test_requires + lint_requires + doc_requires
    },
    entry_points={
        'console_scripts': [
            'planet=planet.cli.cli:main',
        ],
    },
)
