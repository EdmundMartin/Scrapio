import os
import sys
import pathlib
from setuptools import find_packages
from distutils.core import setup


if sys.version_info < (3, 5, 3):
    raise RuntimeError("aiohttp 3.x requires Python 3.5.3+")


here = pathlib.Path(__file__).parent


install_requires = [
    'aiohttp==3.4.4',
    'async-timeout==3.0.0',
    'attrs==18.2.0',
    'chardet==3.0.4',
    'cssselect==1.0.3',
    'idna==2.7',
    'idna-ssl==1.1.0',
    'lxml==4.2.5',
    'multidict==4.4.0',
    'yarl==1.2.6',
]


args = dict(
    name='scrapio',
    version='0.1.3',
    description='Aysncio web crawling framework',
    classifiers=[
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Operating System :: POSIX',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
    ],
    author='Edmund Martin',
    maintainer='Edmund Martin <edmartin101@gmail.com>',
    maintainer_email='edmartin101@gmail.com',
    url='https://github.com/EdmundMartin/Scrapio',
    packages=find_packages(exclude=('tests', '*.tests', '*.tests.*')),
    python_requires='>=3.5.3',
    install_requires=install_requires,
    include_package_data=True,
)

setup(**args)
