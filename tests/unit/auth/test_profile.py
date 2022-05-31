import os
import pathlib
import tempfile
import unittest

from planet.auth.profile import Profile


class ProfileTest(unittest.TestCase):

    def setUp(self):
        self.test_home_dir = tempfile.TemporaryDirectory()
        self.test_home_dir_path = pathlib.Path(self.test_home_dir.name)
        self.old_home = os.environ.get('HOME')
        os.environ['HOME'] = self.test_home_dir.name

    def tearDown(self) -> None:
        if self.old_home:
            os.environ['HOME'] = self.old_home
        else:
            os.environ.pop('HOME')

    def test_filepath_default_none(self):
        under_test = Profile.get_profile_file_path(filename='testfile.dat',
                                                   profile=None,
                                                   override_path=None)
        self.assertIsInstance(under_test, pathlib.Path)
        self.assertEqual(
            pathlib.Path.home().joinpath(".planet/default/testfile.dat"),
            under_test)

    def test_filepath_default_blank(self):
        under_test = Profile.get_profile_file_path(filename='testfile.dat',
                                                   profile='',
                                                   override_path=None)
        self.assertIsInstance(under_test, pathlib.Path)
        self.assertEqual(
            pathlib.Path.home().joinpath(".planet/default/testfile.dat"),
            under_test)

    def test_filepath_default_explicit(self):
        under_test = Profile.get_profile_file_path(filename='testfile.dat',
                                                   profile='default',
                                                   override_path=None)
        self.assertIsInstance(under_test, pathlib.Path)
        self.assertEqual(
            pathlib.Path.home().joinpath(".planet/default/testfile.dat"),
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

    def test_priority_path_override(self):
        under_test = Profile.get_profile_file_path_with_priority(
            filenames=['does_not_exist_1', 'does_not_exist_2'],
            profile='test_profile',
            override_path='/override')
        self.assertEqual(pathlib.Path('/override'), under_test)

    def test_priority_path_fallback(self):
        under_test = Profile.get_profile_file_path_with_priority(
            filenames=['does_not_exist_1', 'does_not_exist_2'],
            profile='test_profile',
            override_path=None)
        self.assertEqual(
            pathlib.Path.home().joinpath(
                ".planet/test_profile/does_not_exist_2"),
            under_test)

    def test_priority_path_first_choice_wins_if_exists(self):
        profile_dir = pathlib.Path.home().joinpath(".planet/test_profile")
        profile_dir.mkdir(parents=True, exist_ok=True)
        pathlib.Path.home().joinpath(
            ".planet/test_profile/does_exist_1").touch()
        under_test = Profile.get_profile_file_path_with_priority(
            filenames=['does_exist_1', 'does_not_exist_2'],
            profile='test_profile',
            override_path=None)
        self.assertEqual(
            pathlib.Path.home().joinpath(".planet/test_profile/does_exist_1"),
            under_test)
