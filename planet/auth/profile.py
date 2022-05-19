import pathlib
from typing import Union


class Profile:

    BUILTIN_PROFILE_NAME_DEFAULT = 'default'
    BUILTIN_PROFILE_NAME_LEGACY = 'legacy'
    BUILTIN_PROFILE_NAME_NONE = 'none'

    @staticmethod
    def get_profile_file_path(
            filename: str,
            profile: Union[str, None],
            override_path: Union[str, pathlib.PurePath, None]) -> pathlib.Path:
        if override_path:
            return pathlib.Path(override_path)
        if not profile or profile == '':
            profile = Profile.BUILTIN_PROFILE_NAME_DEFAULT
        return pathlib.Path.home().joinpath(".planet/{}/{}".format(
            profile.lower(), filename))

    @staticmethod
    def get_profile_file_path_with_priority(
            filenames: list[str],
            profile: Union[str, None],
            override_path: Union[str, pathlib.PurePath, None]) -> pathlib.Path:
        """Given a list of candidate filenames, choose the first that that
        exists. If none exist, the last one will be used.  (Other use cases
        may want 'highest priority is fallback', but we don't need this yet,
        so we haven't written this at this time).  If an override is given, it
        will always be chosen."""
        if override_path:
            return pathlib.Path(override_path)

        last_candidate_path = None
        for candidate_filename in filenames:
            candidate_path = Profile.get_profile_file_path(
                filename=candidate_filename,
                profile=profile,
                override_path=None)
            last_candidate_path = candidate_path
            if candidate_path.exists():
                return candidate_path

        return last_candidate_path

    @staticmethod
    def profile_name_is_default(profile_name: Union[str, None]) -> bool:
        return not profile_name \
                or profile_name == '' \
                or profile_name.lower() == Profile.BUILTIN_PROFILE_NAME_DEFAULT

    @staticmethod
    def profile_name_is_legacy(profile_name: Union[str, None]) -> bool:
        return profile_name \
               and profile_name.lower() == Profile.BUILTIN_PROFILE_NAME_LEGACY

    @staticmethod
    def profile_name_is_none(profile_name: Union[str, None]) -> bool:
        return profile_name \
               and profile_name.lower() == Profile.BUILTIN_PROFILE_NAME_NONE
