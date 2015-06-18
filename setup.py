'''
Copyright 2015 Planet Labs, Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0
   
Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
'''
from codecs import open as codecs_open
from setuptools import setup, find_packages


# Get the long description from the relevant file
try:
    with codecs_open('README.md', encoding='utf-8') as f:
        long_description = f.read()
except:
    # @todo for now, fall back to this - pex fails to resolve the README
    long_description = ''


with open('planet/__init__.py') as f:
    for line in f:
        if line.find("__version__") >= 0:
            version = line.split("=")[1].strip()
            version = version.strip('"')
            version = version.strip("'")
            continue


test_requires = [
    'pytest',
    'mock',
    'requests-mock',
]


setup(name='planet',
      version=version,
      description=u"Planet API Client",
      long_description=long_description,
      classifiers=[],
      keywords='',
      author=u"Ian Schneider",
      author_email='ischneider@planet.com',
      url='https://github.com/planetlabs/planet-client-python',
      license='MIT',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'click',
          'requests',
          'requests_futures>=0.9.5'
      ],
      extras_require={
          'test': test_requires,
          'dev': test_requires + [
              'pex'
          ]
      },
      entry_points="""
      [console_scripts]
      planet=planet.scripts:cli
      """
      )
