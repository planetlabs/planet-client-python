import json
import logging
import planet

logging.basicConfig(level=logging.CRITICAL)


def example_main():
    # Explicitly load the user's auth session from disk for a specific
    # authentication session ("profile").  The user must have invoked
    # `planet auth login` before this program is run or the program
    # must have performed a login() elsewhere prior to this example.
    # If this has not been done, the API calls will fail.  This example
    # will not initialize a new session.
    plsdk_auth = planet.Auth.from_profile(profile_name="my-cli-managed-profile")

    # Create a Planet SDK object that uses the loaded auth session.
    sess = planet.Session(plsdk_auth)
    pl = planet.Planet(sess)

    # Use the SDK to call Planet APIs.
    # Refreshing access tokens will be managed automatically by the SDK.
    for item in pl.data.list_searches():
        print(json.dumps(item, indent=2, sort_keys=True))


if __name__ == '__main__':
    example_main()
