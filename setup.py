from codecs import open as codecs_open
from setuptools import setup, find_packages


# Get the long description from the relevant file
with codecs_open('README.md', encoding='utf-8') as f:
    long_description = f.read()


setup(name='planet',
      version='0.0.1',
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
      ],
      extras_require={
          'test': [
              'pytest',
              'mock',
              'requests-mock',
          ],
      },
      entry_points="""
      [console_scripts]
      planet=planet.scripts:cli
      """
      )
