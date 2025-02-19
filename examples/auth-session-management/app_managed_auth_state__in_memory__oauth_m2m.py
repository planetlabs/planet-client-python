import json
import logging
import planet

logging.basicConfig(level=logging.CRITICAL)


def example_main():
    # Create an auth context with a client ID that
    # is unique to this application.
    plsdk_auth = planet.Auth.from_oauth_m2m(
        client_id="__MUST_BE_END_USER_SUPPLIED__",
        client_secret="__MUST_BE_END_USER_SUPPLIED__",
        save_state_to_disk=False,
    )

    # Explicit login is not required for M2M client use. The above sufficient.
    # plsdk_auth.user_login()

    # Create a Planet SDK object that uses the loaded auth session/
    sess = planet.Session(plsdk_auth)
    pl = planet.Planet(sess)

    # Use the SDK to call Planet APIs.
    # Refreshing access tokens will be managed automatically by the SDK.
    for item in pl.data.list_searches():
        print(json.dumps(item, indent=2, sort_keys=True))


if __name__ == '__main__':
    example_main()
