import json
import planet


def example_main():
    # Create an auth context with a Planet API key loaded from the
    # specified file that was created with older versions of the SDK
    plsdk_auth = planet.Auth.from_file("legacy_api_key_file.json")

    # Explicit login is not required for API key use. The above sufficient.
    # plsdk_auth.user_login()

    # Create a Planet SDK object that uses the loaded auth session
    sess = planet.Session(plsdk_auth)
    pl = planet.Planet(sess)

    # Use the SDK to call Planet APIs.
    for item in pl.data.list_searches():
        print(json.dumps(item, indent=2, sort_keys=True))


if __name__ == '__main__':
    example_main()
