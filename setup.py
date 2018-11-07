

from setuptools import setup, find_packages
from os import path
here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='rse_db',  # Required

    # Versions should comply with PEP 440:
    # https://www.python.org/dev/peps/pep-0440/
    version='1.0.0',  # Required
    description='RSE-DB provides some common tools for working with dbs',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/InstituteforDiseaseModeling/rse_db',
    author='Institute for Disease Modeling - RSE Team',
    author_email='SWResearch@idmod.org',

    # Classifiers help users find your project by categorizing it.
    #
    # For a list of valid classifiers, see https://pypi.org/classifiers/
    classifiers=[  # Optional
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 4 - Beta',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',

        # Pick your license as you wish
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.6',
    ],

    keywords='rse-core',
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),  # Required

    # For an analysis of "install_requires" vs pip's requirements files see:
    # https://packaging.python.org/en/latest/requirements.html
    install_requires=[
        'rse_api>=1.0.0,<1.1',
        'sqlalchemy>=1.2.12,<1.13'
    ],

    extras_require={
        'full': [
            'nose'
        ],
        'dev': ['check-manifest'],
        'test': ['coverage'],
    },
    project_urls={
        'Bug Reports': 'https://github.com/InstituteforDiseaseModeling/rse_db/issues',
        'Source': 'https://github.com/InstituteforDiseaseModeling/rse_db',
    }
)
