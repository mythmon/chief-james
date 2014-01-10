james.py - Chief CLI.

INSTALL
=======

```shell
pip install git+https://github.com/mythmon/chief-james.git
```

USAGE
=====

```
usage: james.py [-h] [-g] [-p] ENV [REF]

positional arguments:
  ENV           Environment defined in the config file to deploy to.
  REF           A git reference (like a SHA) to deploy (default HEAD)

optional arguments:
  -h, --help    show this message and exit
  -g, --github  Open a browser to the Github compare url for the diff.
  -p, --print   Only print the git log (or Github URL with -g), nothing more.
```

CONFIG
======
james.ini in the current directory should be an ini file with
one section per environment. Each environment should have a
`revision_url`, `chief_url`, and `password`. A special section,
`general`, may exist, which will can have one key: `username`. If no
username is given in general, the result of the command "whoami" will be
used.

Example:

```ini
[general]
username = bob

[prod]
revision_url = http://example.com/media/revision.txt
chief_url = http://chief.example.com/example.prod
password = lolpassword

[stage]
revision_url = http://stage.example.com/media/revision.txt
chief_url = http://chief.example.com/example.stage
password = omgsecret
```

Then you can use james.py like this:

    ./james.py stage fa0594dc16df3be505592b6346412c0a03cfe5bf

Answer the questions, and wait a bit, and a deploy will happen! You will
see the same output that you would if you deployed using the website.
