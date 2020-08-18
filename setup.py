import os
from pathlib import Path

from setuptools import setup, find_packages

requirements_file = Path('requirements.txt')
requirements = [line.strip() for line in requirements_file.open()] \
    if requirements_file.exists() else [
        'mapscript', 
        'Jinja2',
        'psycopg2'
    ]

setup(
    name='mapscript_publisher', 
    version='0.5', 
    packages=['map_pub'], 
    install_requires=requirements, 
    include_package_data=True,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Natural Language :: Russian',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.5',
    ],
)