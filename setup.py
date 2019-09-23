from setuptools import setup, find_packages

setup(
    name='mapscript_publisher', 
    version='0.4', 
    packages=['map_pub'], 
    install_requires=[
        'mapscript', 
        'Jinja2',
        'psycopg2'
    ]
)