from setuptools import setup, find_packages


setup(
    name='wadutils',
    version='0.6',
    author='Samar Agrawal',
    author_email='samar.agrawal@wadi.com',
    packages = find_packages(),
    package_dir = {'': '.'},
    classifiers=[
        'Development Status :: 1 - Alpha',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],
    zip_safe=True,
)


