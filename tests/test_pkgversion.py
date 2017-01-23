#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_pkgversion
----------------------------------

Tests for `pkgversion` module.
"""
import ast
import os
import re
from subprocess import PIPE, Popen

from pkgversion import (
    get_git_repo_dir, get_version, list_requirements, pep440_version,
    write_setup_py,
)

requirements_file = os.path.join(
    os.path.dirname(__file__), 'fixtures/requirements.txt'
)


class TestPkgversion(object):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_get_version(self):
        assert re.match(r'^(\d.\d(.\d))?(-\d+-\w+)?', get_version())

    def test_pep440_version(self):
        assert pep440_version('1.2') == '1.2'
        assert pep440_version('1.2.3') == '1.2.3'
        assert pep440_version('1.2.3-99-ge3b6e92') == '1.2.3+99.ge3b6e92'
        assert pep440_version('ge3b6e92') == '0.0+ge3b6e92'
        assert pep440_version(None) is None
        assert pep440_version('1.2.3a4-99-ge3b6e92') == '1.2.3a4+99.ge3b6e92'
        assert pep440_version('1.2.3-a4-99-ge3b6e92') == '1.2.3a4+99.ge3b6e92'
        assert pep440_version('1.2.3_a4-99-ge3b6e92') == '1.2.3a4+99.ge3b6e92'
        assert pep440_version('1.2.3.a4-99-ge3b6e92') == '1.2.3a4+99.ge3b6e92'
        assert pep440_version('1.2.3-a4') == '1.2.3a4'
        assert pep440_version('1.2.3a4') == '1.2.3a4'
        assert pep440_version('1.2.3-alpha4') == '1.2.3a4'
        assert pep440_version('1.2.3-beta4') == '1.2.3b4'
        assert pep440_version('1.2.3-rc4') == '1.2.3rc4'
        assert pep440_version('1.2.3-c4') == '1.2.3rc4'
        assert pep440_version('1.2.3-preview4') == '1.2.3rc4'
        assert pep440_version('1.2.3-pre4') == '1.2.3rc4'
        assert pep440_version('1.2.3b4') == '1.2.3b4'
        assert pep440_version('1.2.3.rc4') == '1.2.3rc4'
        assert pep440_version('1.2.3.dev4') == '1.2.3.dev4'
        assert pep440_version('1.2.3ndev4') is None
        assert pep440_version('1.2.3.post1') == '1.2.3.post1'
        assert pep440_version('1.2.3npost1') is None
        assert pep440_version('1.2.3-a4.post1.dev5') == '1.2.3a4.post1.dev5'
        assert pep440_version('1.2.3-a4.post1.dev5') == '1.2.3a4.post1.dev5'
        assert pep440_version('non1.2.3.post1') is None

    def test_list_requirements(self):
        actual = list_requirements(requirements_file)
        expected = [
            'unversioned', 'pinned_version==1.0',
            'ranged_version<=2,>=1.0', 'url', 'unversioned_url',
            'editable'
        ]
        assert actual == expected

    def test_get_git_repo_dir(self):
        assert os.path.isdir(get_git_repo_dir())
        assert os.path.isdir(os.path.join(get_git_repo_dir(), '.git'))

    def test_get_git_repo_dir_invalid(self):
        pwd = os.getcwd()
        os.chdir('/tmp')
        assert get_git_repo_dir() is None
        os.chdir(pwd)

    def test_write_setup_py_with_git_repo(self, tmpdir):
        try:
            prev_cwd = os.getcwd()
            os.chdir(str(tmpdir))

            commands = [
                ['git', 'init'],
                ['git', 'config', 'user.email', 'me@example.com'],
                ['git', 'config', 'user.name', 'me'],
                ['touch', 'somefile'],
                ['git', 'add', 'somefile'],
                ['git', 'commit', '-m', 'first'],
                ['git', 'tag', '2.0.1']
            ]
            for command in commands:
                Popen(command, stdout=PIPE, cwd=str(tmpdir)).communicate()

            expected_import = "^from setuptools import setup$"
            expected_setup = "^setup\(\*\*(.*)\)$"

            write_setup_py(
                install_requires=['test']
            )
            with open('setup.py', 'r') as f:
                generated = f.read().splitlines()
                assert 3 == len(generated)
                blank_line = generated[0]
                import_line = generated[1]
                setup_line = generated[2]
                assert '' == blank_line
                assert re.match(expected_import, import_line) is not None
                setup_args_match = re.match(expected_setup, setup_line)
                assert setup_args_match is not None
                d = ast.literal_eval(setup_args_match.groups()[0])
                assert 2 == len(d)
                assert '2.0.1' == d['version']
                assert ['test'] == d['install_requires']
        finally:
            os.chdir(prev_cwd)
