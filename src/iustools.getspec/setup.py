
from setuptools import setup, find_packages
import sys, os

# You probably want to change the name, this is a healthy default for paster
setup(name='iustools.getspec',
    version='0.1',
    description='Getspec plugin for Iustools',
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
        "genshi",
        "cement >=0.8.16, <0.9",
        "iustools.core",
        ],
    setup_requires=[
        ],
    test_suite='nose.collector',
    entry_points="""
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
