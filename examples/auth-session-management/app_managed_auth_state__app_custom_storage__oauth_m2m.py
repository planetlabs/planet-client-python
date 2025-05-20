import json
import logging
import os
import pathlib
import stat

import planet

from planet_auth import ObjectStorageProvider, ObjectStorageProvider_KeyType

logging.basicConfig(level=logging.CRITICAL)


class DemoStorageProvider(ObjectStorageProvider):
    """
    Simple demo custom storage provider that uses
    ~/.planet-demo as a storage home for saving object.

    As a practical matter, ObjectStorageProvider_KeyType is defined
    to be pathlib.Path, and we leverage that in this example.
    But, storage providers are not required to use the local file
    system to store objects.
    """

    def __init__(self):
        self._demo_storage_root = pathlib.Path.home() / ".planet-demo"

    def load_obj(self, key: ObjectStorageProvider_KeyType) -> dict:
        demo_obj_filepath = self._demo_obj_filepath(key)
        return self._load_file(file_path=demo_obj_filepath)

    def save_obj(self, key: ObjectStorageProvider_KeyType, data: dict) -> None:
        demo_obj_filepath = self._demo_obj_filepath(key)
        self._save_file(file_path=demo_obj_filepath, data=data)

    def obj_exists(self, key: ObjectStorageProvider_KeyType) -> bool:
        demo_obj_filepath = self._demo_obj_filepath(key)
        return demo_obj_filepath.exists()

    def mtime(self, key: ObjectStorageProvider_KeyType) -> float:
        obj_filepath = self._demo_obj_filepath(key)
        return obj_filepath.stat().st_mtime

    def obj_rename(self,
                   src: ObjectStorageProvider_KeyType,
                   dst: ObjectStorageProvider_KeyType) -> None:
        src_filepath = self._demo_obj_filepath(src)
        dst_filepath = self._demo_obj_filepath(dst)
        src_filepath.rename(dst_filepath)

    def _demo_obj_filepath(self, obj_key):
        if obj_key.is_absolute():
            obj_path = self._demo_storage_root / obj_key.relative_to("/")
        else:
            obj_path = self._demo_storage_root / obj_key
        return obj_path

    @staticmethod
    def _load_file(file_path: pathlib.Path) -> dict:
        logging.debug(msg="Loading JSON data from file {}".format(file_path))
        with open(file_path, mode="r", encoding="UTF-8") as file_r:
            return json.load(file_r)

    @staticmethod
    def _save_file(file_path: pathlib.Path, data: dict):
        file_path.parent.mkdir(parents=True, exist_ok=True)
        logging.debug(msg="Writing JSON data to file {}".format(file_path))
        with open(file_path, mode="w", encoding="UTF-8") as file_w:
            os.chmod(file_path, stat.S_IREAD | stat.S_IWRITE)
            _no_none_data = {
                key: value
                for key, value in data.items() if value is not None
            }
            file_w.write(json.dumps(_no_none_data, indent=2, sort_keys=True))


def example_main():
    # Create an auth context with the client ID and secret of the service account.
    plsdk_auth = planet.Auth.from_oauth_m2m(
        client_id="__MUST_BE_END_USER_SUPPLIED__",
        client_secret="__MUST_BE_END_USER_SUPPLIED__",
        profile_name="my-example-name-m2m-with-custom-storage",
        save_state_to_storage=True,
        storage_provider=DemoStorageProvider(),
    )

    # Explicit login is not required for M2M client use. The above sufficient.
    # plsdk_auth.user_login()

    # Create a Planet SDK object that uses the loaded auth session.
    sess = planet.Session(plsdk_auth)
    pl = planet.Planet(sess)

    # Use the SDK to call Planet APIs.
    # Refreshing access tokens will be managed automatically by the SDK.
    for item in pl.data.list_searches():
        print(json.dumps(item, indent=2, sort_keys=True))


if __name__ == '__main__':
    example_main()
