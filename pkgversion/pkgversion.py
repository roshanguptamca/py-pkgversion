# -*- coding: utf-8 -*-
import locale
import os
import pprint
import re
from subprocess import PIPE, Popen

from pip.download import PipSession
from pip.req import parse_requirements


setup_py_template = """
from setuptools import setup
setup(**{0})
"""


def get_git_repo_dir():
    """
    Get the directory of the current git project

    Returns:
        str: The top level directory of the current git project
    """
    repo_dir, err = Popen(
        ['git', 'rev-parse', '--show-toplevel'],
        stdin=PIPE, stderr=PIPE, stdout=PIPE).communicate()
    repo_dir = repo_dir.strip()
    if not repo_dir:
        repo_dir = None

    if repo_dir and not isinstance(repo_dir, str):

        encoding = locale.getpreferredencoding()

        if encoding:
            return repo_dir.decode(encoding)

    return repo_dir


def list_requirements(path):
    """
    Create a list of requirements suited for ``setup.py``

    Example code::

        list_requirements('path/to/file.txt')
        ['pytest==2.7.2', 'pytest-django==2.8.0']

    Args:
        str path: Path to the requirements file

    Returns:
        list: List of packages
    """
    return [str(r.req) for r in parse_requirements(path, session=PipSession())]


def get_version():
    """
    Retrieve the version from git using ``git describe --always --tags``

    Returns:
        str: The version in the format of ``2.0.0+43.gebecdc8``
    """
    cmd = ['git', 'describe', '--always', '--tags']
    p = Popen(cmd, stdout=PIPE, close_fds=True)
    version = p.stdout.read().strip()
    return str(version) or "0.0.0"


def match_tail(regex, text):
    complete_regex = r'\A(?P<head>.+?)(?P<tail>' + regex + r')\Z'
    v = re.compile(complete_regex).match(text)
    if v:
        return v.group('head'), v
    else:
        return text, None


def pep440_version(version=get_version()):
    """
    Format the version according to the ``PEP 440`` spec.

    >>> pep440_version('2.0.0-43-gebecdc8')
    '2.0.0+43.gebecdc8'

    >>> pep440_version('2.0.0')
    '2.0.0'

    Args:
        str version: String of the version.

        Public version according to PEP 440.

        Optionally may have postfix produced by git describe:
        -<number-commits>-g<hashid>

    Returns:
        str: PEP 440 formatted version string

    """
    if version:
        v = re.compile(r'\A(?P<githash>g\w+)\Z').match(version)
        if v:
            return '0.0+' + v.group('githash')

        parts = []

        head, match = match_tail(r'-(?P<gitnr>\d+)-(?P<githash>g\w+)', version)
        if match:
            parts.insert(0, '+' + match.group('gitnr') + '.' + match.group('githash'))

        head, match = match_tail(r'\.dev\d+', head)
        if match:
            parts.insert(0, match.group('tail'))

        head, match = match_tail(r'\.post\d+', head)
        if match:
            parts.insert(0, match.group('tail'))

        head, match = match_tail(r'[-\._]?(?P<prerelease>a|alpha|b|beta|c|rc|pre|preview)(?P<version>\d+)', head)
        if match:
            prerelease = {
                'alpha': 'a', 'a': 'a',
                'beta': 'b', 'b': 'b',
                'c': 'rc',
                'pre': 'rc', 'preview': 'rc', 'rc': 'rc'
            }[match.group('prerelease')]
            parts.insert(0, prerelease + match.group('version'))

        v = re.compile(r'\A(?P<release>\d+\.\d+(\.\d+)?)\Z').match(head)
        if not v:
            return None

        parts.insert(0, v.group('release'))

        return ''.join(parts)

    return None


def write_setup_py(file=None, **kwargs):
    """
    Write the setup.py according to a template with variables.
    This is mainly to avoid the dependency requirement on installing packages
    that rely on this package.
    """
    data = dict(version=get_version())
    data.update(kwargs)

    if not file:
        file = os.path.join(get_git_repo_dir(), 'setup.py')

    with open(file, 'w+') as f:
        f.write(setup_py_template.format(pprint.pformat(data)))
