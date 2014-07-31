#!/usr/bin/env python
from distutils.core import setup, Extension

setup(
    name='wavetool',
    description='Wave Manipulation/Analysis Tools',
    license='MIT/X',
    author='Yusuke Shinyama',
    author_email='yusuke at cs dot nyu dot edu',
    packages=[
        ],
    scripts=[
        ],
    ext_modules=[
        Extension(
            'wavcorr',
            ['wavcorr.c'],
            #define_macros=[],
            #include_dirs=[],
            #library_dirs=[],
            #libraries=[],
            )
        ],
    )
