import json
import planet
import sys


def example_main():
    # Explicitly load the user's auth session from disk.  The user must have
    # invoked `planet auth login` before this program is run, or the API calls
    # will fail.  This will not initialize a new session.
    plsdk_auth = planet.Auth.from_user_default_session()

    if not plsdk_auth.is_initialized():
        print(
            "Login required. Execute the following command:\n\n\tplanet auth login\n"
        )
        sys.exit(99)

    # Create a Planet SDK object that uses the loaded auth session.
    sess = planet.Session(plsdk_auth)
    pl = planet.Planet(sess)

    # Use the SDK to call Planet APIs.
    # Refreshing access tokens will be managed automatically by the SDK.
    for item in pl.data.list_searches():
        print(json.dumps(item, indent=2, sort_keys=True))


if __name__ == '__main__':
    example_main()
