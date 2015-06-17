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
