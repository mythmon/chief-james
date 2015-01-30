import sys
from setuptools import setup

install_requires = [
    'requests>=2.2.1',
]

# only install those requirements on Python 2.x as 3.x supports SNI
if sys.version_info[:2] < (3,):
    install_requires.append([
        'ndg-httpsclient>=0.3.2',
        'pyOpenSSL>=0.14',
        'pyasn1>=0.1.7',
    ])


setup(
    name='chief-james',
    version='1.0',
    py_modules=['james'],
    author='Mike Cooper',
    license='MPL 2.0',
    author_email='mcooper@mozilla.com',
    url='https://github.com/mythmon/chief-james',
    install_requires=install_requires,
    entry_points={'console_scripts': ['james = james:main']},
)
