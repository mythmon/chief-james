from distutils.core import setup

with open('requirements.txt') as f:
    requirements = [l.strip() for l in f]

setup(
    name='chief-james',
    version='0.1',
    modules=['james'],
    scripts=['james.py'],
    author='Mike Cooper',
    author_email='mcooper@mozilla.com',
    url='https://github.com/mythmon/chief-james',
    install_requires=requirements,
    package_data={'james': ['requirements.txt', 'README', 'LICENSE']}
)
