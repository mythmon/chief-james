# To run these tests, you need the following:
#
# * nosetests
# * mock
#
# Then you do:
#
#    $ nosetests

from mock import patch
from nose.tools import eq_

import james


def test_extract_bugs():
    data = [
        (['78e7585 Change webhook desc'], []),

        (['a230011 [bug 933068] Add Uruguay'], ['933068']),

        (['a230011 [bug 933068] Add Uruguay'], ['933068']),

        (['a230011 [bug 933068] Add Uruguay',
          '45ab721 [bug 933068] Add Peru and Mexico'],
         ['933068']),

        (['2d2566e [bug 918959] Strip that whitespace!',
          '45ab721 [bug 933068] Add Peru and Mexico'],
         ['918959', '933068']),
    ]

    for changelog, bugids in data:
        eq_(james.extract_bugs(changelog), bugids)


def test_generate_desc():
    # Pushing multiple things with bug numbers
    with patch('james.git') as mock_git:
        mock_git.return_value = (
            'a230011 [bug 933068] Add Uruguay\n'
            '45ab721 [bug 933068] Add Peru and Mexico\n'
            '167143d [bug 754615] Add url as related link to Atom feed\n'
        )

        eq_(james.generate_desc('167143d', 'a230011'),
            'Fixing: bug #754615, bug #933068')

    # Pushing multiple things with no bug numbers
    with patch('james.git') as mock_git:
        mock_git.return_value = (
            'a230011 Add Uruguay\n'
            '45ab721 Add Peru and Mexico\n'
            '167143d Add url as related link to Atom feed\n'
        )

        desc = james.generate_desc('167143d', 'a230011')
        assert desc.startswith('No bugfixes')

    # Pushing it again
    with patch('james.git') as mock_git:
        mock_git.return_value = 'b27dde9 Add LG Fireweb\n'

        eq_(james.generate_desc('b27dde9', 'b27dde9'),
            'Pushing b27dde9 again')
