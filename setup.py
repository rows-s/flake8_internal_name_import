from setuptools import setup

setup(
    name='flake8_private_name_import',
    version='0.1.5',
    description="flake8 plugin that reports imports of private names",
    long_description="flake8 plugin that reports imports of private names",
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
    keywords='python pep8 flake8 private import',
    author='Vladimir Marmuz',
    author_email='vladimir.rows@gmail.com',
    url='https://github.com/rows-s/flake8_private_name_import',
    license='MIT',
    py_modules=['flake8_private_name_import'],
    include_package_data=True,
    test_suite='run_tests',
    zip_safe=False,
    install_requires=['flake8 >= 3.3.0'],
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'flake8.extension': [
            'PNI00 = flake8_private_name_import:Plugin',
        ],
    },
)
