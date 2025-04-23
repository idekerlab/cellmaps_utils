#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""
import os
import re
from setuptools import setup, find_packages


with open(os.path.join('cellmaps_utils', '__init__.py')) as ver_file:
    for line in ver_file:
        line = line.rstrip()
        if line.startswith('__version__'):
            version = re.sub("'", "", line[line.index("'"):])
        elif line.startswith('__description__'):
            desc = re.sub("'", "", line[line.index("'"):])
        elif line.startswith('__repo_url__'):
            repo_url = re.sub("'", "", line[line.index("'"):])
        elif line.startswith('__author__'):
            author = re.sub("'", "", line[line.index("'"):])
        elif line.startswith('__email__'):
            email = re.sub("'", "", line[line.index("'"):])

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()


requirements = ['fairscape-cli==1.0.2',
                'ndex2>=3.8.0,<4.0.0',
                'scipy>=1.10.1,<1.13.0',
                'scikit-learn>=0.19.0,<1.4.0',
                'pandas>=2.0.0,<3.0.0',
                'numpy>=1.24.4,<2.0.0',
                'dill>=0.3.8,<0.4.0',
                'tqdm>=4.66.6,<5.0.0',
                'requests>=2.31.0,<3.0.0']

setup_requirements = [ ]
test_requirements = ['pytest']
setup(
    author=author,
    author_email=email,
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11'
    ],
    description=desc,
    install_requires=requirements,
    license="MIT license",
    long_description=readme + '\n\n' + history,
    long_description_content_type='text/x-rst',
    include_package_data=True,
    keywords='cellmaps_utils',
    name='cellmaps_utils',
    packages=find_packages(include=['cellmaps_utils']),
    package_dir={'cellmaps_utils': 'cellmaps_utils'},
    package_data={'cellmaps_utils': ['apms_readme.txt',
                                     'crispr_readme.txt',
                                     'ifimage_readme.txt']},
    scripts=['cellmaps_utils/cellmaps_utilscmd.py'],
    setup_requires=setup_requirements,
    tests_require=test_requirements,
    url=repo_url,
    version=version,
    zip_safe=False)
