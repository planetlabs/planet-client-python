import pathlib
import unittest

from planet.auth.auth import Profile


class ProfileTest(unittest.TestCase):

    def test_filepath_default_none(self):
        under_test = Profile.get_profile_file_path(filename='testfile.dat',
                                                   profile=None,
                                                   override_path=None)
        self.assertIsInstance(under_test, pathlib.Path)
        self.assertEqual(pathlib.Path.home().joinpath(".planet/testfile.dat"),
                         under_test)

    def test_filepath_default_blank(self):
        under_test = Profile.get_profile_file_path(filename='testfile.dat',
                                                   profile='',
                                                   override_path=None)
        self.assertIsInstance(under_test, pathlib.Path)
        self.assertEqual(pathlib.Path.home().joinpath(".planet/testfile.dat"),
                         under_test)

    def test_filepath_default_explicit(self):
        under_test = Profile.get_profile_file_path(filename='testfile.dat',
                                                   profile='default',
                                                   override_path=None)
        self.assertIsInstance(under_test, pathlib.Path)
        self.assertEqual(pathlib.Path.home().joinpath(".planet/testfile.dat"),
                         under_test)

    def test_filepath_default_override(self):
        under_test = Profile.get_profile_file_path(filename='testfile.dat',
                                                   profile='',
                                                   override_path='/override')
        self.assertIsInstance(under_test, pathlib.Path)
        self.assertEqual(pathlib.Path("/override"), under_test)

    def test_filepath_named_default(self):
        under_test = Profile.get_profile_file_path(filename='testfile.dat',
                                                   profile='test_profile',
                                                   override_path=None)
        self.assertIsInstance(under_test, pathlib.Path)
        self.assertEqual(
            pathlib.Path.home().joinpath(".planet/test_profile/testfile.dat"),
            under_test)

    def test_pathfile_named_override(self):
        under_test = Profile.get_profile_file_path(filename='testfile.dat',
                                                   profile='test_profile',
                                                   override_path='/override')
        self.assertIsInstance(under_test, pathlib.Path)
        self.assertEqual(pathlib.Path("/override"), under_test)
