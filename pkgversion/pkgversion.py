# -*- coding: utf-8 -*-
import os
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


def pep440_version(version=get_version()):
    """
    Format the version according to the ``PEP 440`` spec.

    >>> pep440_version('2.0.0-43-gebecdc8')
    '2.0.0+43.gebecdc8'

    >>> pep440_version('2.0.0')
    '2.0.0'

    Args:
        str version: String of the version

    Returns:
        str: PEP 440 formatted version string

    """
    if version:
        v = re.compile(r'(\d+\.\d+(\.\d+)?)(-(\d+)-(\w+))?').search(version)
        if v.group(5):
            return "{0}+{1}.{2}".format(v.group(1), v.group(4), v.group(5))
        else:
            return v.group(1)
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
        f.write(setup_py_template.format(data))
