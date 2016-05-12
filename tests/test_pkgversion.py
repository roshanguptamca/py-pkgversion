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
import tempfile
import unittest

from pkgversion import (
    get_git_repo_dir, get_version, list_requirements, pep440_version,
    write_setup_py,
)

requirements_file = os.path.join(
    os.path.dirname(__file__), 'fixtures/requirements.txt'
)


class TestPkgversion(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_get_version(self):
        self.assertRegexpMatches(get_version(), r'^(\d.\d(.\d))?(-\d+-\w+)?')

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

    def test_write_setup_py(self):
        expected_import = "^from setuptools import setup$"
        expected_setup = "^setup\(\*\*(.*)\)$"
        _, tmp_file = tempfile.mkstemp()
        write_setup_py(
            file=tmp_file,
            version='1.0.0',
            install_requires=['test']
        )
        try:
            with open(tmp_file, 'r') as f:
                generated = f.read().splitlines()
                self.assertEqual(3, len(generated))
                blank_line = generated[0]
                import_line = generated[1]
                setup_line = generated[2]
                self.assertEqual('', blank_line)
                assert re.match(expected_import, import_line) is not None
                setup_args_match = re.match(expected_setup, setup_line)
                assert setup_args_match is not None
                d = ast.literal_eval(setup_args_match.groups()[0])
                self.assertEqual(2, len(d))
                self.assertEqual('1.0.0', d['version'])
                self.assertEqual(['test'], d['install_requires'])
        finally:
            os.remove(tmp_file)


if __name__ == '__main__':
    import sys

    sys.exit(unittest.main())
