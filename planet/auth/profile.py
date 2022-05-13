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
