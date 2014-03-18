#!/usr/bin/env python
"""
james.py - Chief CLI.

USAGE: james.py ENV REF
  ENV - Environment defined in the config file to deploy to.
  REF - A git reference (like a SHA) to deploy.

Config: james.ini in the current directory should be an ini file with
one section per environment. Each environment should have a
`revision_url`, `chief_url`, and `password`. A special section,
`general`, may exist, which will can have one key: `username`. If no
username is given in general, the result of the command "whoami" will be
used.

Example Config:

    [general]
    username = bob
    github = bobloblaw/lawblog

    [prod]
    revision_url = http://example.com/media/revision.txt
    chief_url = http://chief.example.com/example.prod
    password = lolpassword

    [stage]
    revision_url = http://stage.example.com/media/revision.txt
    chief_url = http://chief.example.com/example.stage
    password = omgsecret

Then you can use james.py like this:

    ./james.py stage fa0594dc16df3be505592b6346412c0a03cfe5bf

Answer the questions, and wait a bit, and a deploy will happen! You will
see the same output that you would if you deployed using the website.

Dependencies: requests
"""


import argparse
import os
import random
import re
import subprocess
import sys
import time
import webbrowser
from ConfigParser import ConfigParser, NoOptionError, NoSectionError

import requests


URL_TEMPLATE = 'https://github.com/{repo}/compare/{rev}...{branch}'
HASH_LEN = 8


def get_random_desc():
    return random.choice([
        'No bugfixes--must be adding infinite loops.',
        'No bugfixes--must be rot13ing function names for code security.',
        'No bugfixes--must be demonstrating our elite push technology.',
        'No bugfixes--must be testing james.',
    ])


def git(*args, **kwargs):
    args = ['git'] + list(args)
    if kwargs.pop('out', None) == 'print':
        subprocess.check_call(args, **kwargs)
        return None
    else:
        return subprocess.check_output(args, **kwargs)


def config(environment, key, required=False, memo={}):
    if 'config' not in memo:
        memo['config'] = ConfigParser()
        memo['config'].read('james.ini')

    try:
        return memo['config'].get(environment, key)
    except NoSectionError:
        if required:
            print 'No such environment %s' % environment
            sys.exit(2)
    except NoOptionError:
        if required:
            print 'Missing key %s in environment %s' % (key, environment)
            sys.exit(4)

    return None


def usage():
    print 'USAGE: %s ENV [REF]' % os.path.split(sys.argv[0])[-1]
    print '  ENV - Environment defined in the config file to deploy to.'
    print '  REF - A git reference (like a SHA) to deploy (default HEAD)'


def check_ancestry(older, newer):
    commits = git('rev-list', newer).split('\n')
    return older in commits


def yes_no(prompt):
    sys.stdout.write(prompt + ' ')
    ret = raw_input('[y/n] ')
    while ret not in ['y', 'n']:
        ret = raw_input('Please choose "y" or "n" [y/n] ')
    return ret == 'y'


def username():
    username = config('general', 'username')

    if username is None:
        username = subprocess.check_output(['whoami'])

    return username.strip()


def get_environment_commit(environment):
    revision_url = config(environment, 'revision_url', required=True)
    if not revision_url.startswith('http'):
        revision_url = 'http://' + revision_url
    return requests.get(revision_url).text.strip()


def get_compare_url(env_rev, new_rev=None):
    repo = config('general', 'github', required=True)
    return URL_TEMPLATE.format(rev=env_rev[:HASH_LEN],
                               branch=new_rev[:HASH_LEN],
                               repo=repo)


def extract_bugs(changelog):
    """Takes output from git log --oneline and extracts bug numbers"""
    bug_regexp = re.compile(r'\bbug (\d+)\b', re.IGNORECASE)
    bugs = set()
    for line in changelog:
        for bug in bug_regexp.findall(line):
            bugs.add(bug)

    return sorted(list(bugs))


def generate_desc(from_commit, to_commit, changelog):
    # Figure out a good description based on what we're pushing
    # out.
    if from_commit.startswith(to_commit):
        desc = 'Pushing {0} again'.format(to_commit)
    else:
        bugs = extract_bugs(changelog.split('\n'))
        if bugs:
            bugs = ['bug #{0}'.format(bug) for bug in bugs]
            desc = 'Fixing: {0}'.format(', '.join(bugs))
        else:
            desc = get_random_desc()
    return desc


def webhooks(env, environment_commit, local_commit):
    if config(env, 'newrelic'):
        print 'Running New Relic deploy hook...',
        log_spec = '{0}..{1}'.format(environment_commit, local_commit)
        changelog = git('log', '--pretty=oneline', log_spec)

        desc = generate_desc(environment_commit, local_commit, changelog)

        rev = changelog.split('\n')[0].split(' ')[0]

        data = {
            'app_name': config('newrelic', 'app_name', required=True),
            'application_id': config('newrelic', 'application_id',
                                     required=True),
            'description': desc,
            'revision': rev,
            'changelog': changelog,
            'user': username(),
        }
        url = 'https://rpm.newrelic.com/deployments.xml'
        data = dict(('deployment[%s]' % k, v) for k, v in data.items())
        headers = {'x-api-key':  config('newrelic', 'api_key', required=True)}

        res = requests.post(url, data=data, headers=headers)
        print res.status_code, res.text

        print 'done'


def main():
    parser = argparse.ArgumentParser(description='Push code using Chief.')
    parser.add_argument('env', metavar='ENV',
                        help='Environment defined in the config file to deploy to.')
    parser.add_argument('ref', metavar='REF', nargs='?', default='HEAD',
                        help='A git reference (like a SHA) to deploy (default HEAD)')
    parser.add_argument('-g', '--github', action='store_true',
                        help='Open a browser to the Github compare url for the diff.')
    parser.add_argument('-p', '--print', action='store_true', dest='print_only',
                        help='Only print the git log (or Github URL with -g), nothing more.')
    args = parser.parse_args()

    environment = args.env
    commit = args.ref

    environment_commit = get_environment_commit(environment)
    local_commit = git('rev-parse', commit).strip()

    if args.github:
        url = get_compare_url(environment_commit, local_commit)
        print url
        if not args.print_only:
            webbrowser.open(url)
        return 0

    chief_url = config(environment, 'chief_url', required=True)
    password = config(environment, 'password', required=True)

    if not chief_url.startswith('http'):
        chief_url = 'http://' + chief_url

    print 'Environment: {0}'.format(environment)
    print 'Pushing as : {0}'.format(username())
    print 'Pushing    : {0} ({1})'.format(commit, local_commit[:HASH_LEN])
    print 'On server  : {0}'.format(environment_commit[:HASH_LEN])

    log_spec = environment_commit + '..' + local_commit

    if environment_commit.startswith(local_commit):
        print 'Pushing out (again):'
        git('log', '--oneline', '-n', '1', local_commit, out='print')

    elif not check_ancestry(environment_commit, local_commit):
        print 'Pushing from different branch:'
        git('log', '--oneline', '-n', '1', local_commit, out='print')

    else:
        print 'Pushing out:'
        git('log', '--oneline', log_spec, out='print')

    if args.print_only:
        return 0

    print ''

    if yes_no('Proceed?'):
        payload = {
            'who': username(),
            'password': password,
            'ref': local_commit,
        }

        print ('Logs at: {0}/logs/{1}'.format(chief_url, local_commit))

        start_time = time.time()
        try:
            res = requests.post(chief_url, data=payload, stream=True)
        except requests.RequestException:
            print 'Error connecting to Chief. Did you connect to the VPN?'
            return 1

        for chunk in res.iter_content():
            sys.stdout.write(chunk)
            sys.stdout.flush()

        # Chief doesn't finish with a newline. Rude.
        print ''

        end_time = time.time()
        print 'Total time: {0}'.format(end_time - start_time)

        webhooks(environment, environment_commit, local_commit)

    else:
        print 'Canceled!'
        return 1


if __name__ == '__main__':
    sys.exit(main())
