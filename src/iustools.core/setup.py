
from setuptools import setup, find_packages
import sys, os

setup(name='iustools.core',
    version='0.1.6',
    description='Scripts and Utilities for The IUS Community Project',
    classifiers=[], 
    keywords='',
    author='IUS CoreDev Team',
    author_email='coredev@iuscommunity.org',
    url='http://iuscommunity.org',
    license='GNU GPLv2',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        "configobj",
        # remove if not using genshi templating
        "genshi",
        "cement >=0.8.16, <0.9",
        "monkeyfarm.core >=2.0.3",
        "monkeyfarm.interface >=2.0.3",
        ],
    setup_requires=[
        # uncomment for nose testing
        # "nose",
        ],
    test_suite='nose.collector',
    entry_points="""
    [console_scripts]
    ius = iustools.core.appmain:main
    """,
    namespace_packages=[
        'iustools', 
        'iustools.lib', 
        'iustools.bootstrap',
        'iustools.controllers',
        'iustools.model',
        'iustools.helpers',
        'iustools.templates',
        ],
    )
