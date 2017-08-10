from setuptools import setup, find_packages


setup(
    name='wadutils',
    version='1.3',
    author='Samar Agrawal',
    author_email='samar.agrawal@wadi.com',
    packages = find_packages(),
    package_dir = {'': '.'},
    install_requires=[
        "pyshorteners",
        "gspread",
        "pyopenssl",
        "oauth2client==1.5.2",
        "boto",
        "pyyaml",
        "sqlalchemy",
        "dropbox",
        "requests",
        "hirlite",
        "requests_ntlm",
        "lxml",
        "graypy",
        "pika",
        "pika_pool"
    ],
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


