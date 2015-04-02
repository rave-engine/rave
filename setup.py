import configparser
from setuptools import setup

# Read configuration from setup.cfg
parser = configparser.ConfigParser()
parser.read('setup.cfg')

config = { key.replace('-', '_'): value for key, value in parser['metadata'].items() }
setup(**config)
