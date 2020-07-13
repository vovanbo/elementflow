from setuptools import setup

setup(
    name='elementflow',
    version='0.5',
    author='Ivan Sagalaev',
    author_email='maniac@softwaremaniacs.org',
    url='https://github.com/isagalaev/elementflow',
    license='BSD',
    description='Python library for generating XML as a stream without building a tree in memory.',
    long_description=open('README.md').read(),

    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    extras_require={
        'test': [
            'pytest',
            'tox',
        ]
    },
    py_modules=['elementflow'],
)
