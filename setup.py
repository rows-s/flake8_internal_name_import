from setuptools import setup

long_description = """\
Flake8 plugin that reports imports of internal names.

Visit github for codes, options and examples: https://github.com/rows-s/flake8_internal_name_import
"""

setup(
    name='flake8_internal_name_import',
    version='1.0.0',
    description="flake8 plugin that reports imports of internal names",
    long_description=long_description,
    # Get more from https://pypi.org/classifiers/
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Framework :: Flake8',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: Implementation :: CPython',
        'Topic :: Software Development',
        'Topic :: Software Development :: Quality Assurance',
    ],
    python_requires='>=3.7',
    keywords='python pep8 flake8 internal import',
    author='Vladimir Marmuz',
    author_email='vladimir.rows@gmail.com',
    url='https://github.com/rows-s/flake8_internal_name_import',
    license='MIT',
    py_modules=['flake8_internal_name_import'],
    include_package_data=True,
    test_suite='pytest',
    zip_safe=False,
    install_requires=['flake8 >= 3.3.0'],
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'flake8.extension': [
            'PNI00 = flake8_internal_name_import:Plugin',
        ],
    },
)
