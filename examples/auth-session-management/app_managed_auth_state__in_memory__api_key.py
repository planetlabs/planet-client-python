import json
import planet


def example_main():
    # Create an auth context with the specified API key
    plsdk_auth = planet.Auth.from_key(
        key="__PLANET_API_KEY_MUST_BE_END_USER_SUPPLIED__")

    # Explicit login is not required for API key use. The above sufficient.
    # plsdk_auth.user_login()

    # Create a Planet SDK object that uses the loaded auth session
    sess = planet.Session(plsdk_auth)
    pl = planet.Planet(sess)

    # Use the SDK to call Planet APIs
    for item in pl.data.list_searches():
        print(json.dumps(item, indent=2, sort_keys=True))


if __name__ == '__main__':
    example_main()
