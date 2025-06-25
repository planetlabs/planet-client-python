import json
import planet


def initialize_user_session(plsdk_auth):
    # Example of initiating a user session where the app is 100%
    # responsible for the user experience.

    # 1. Initiate the login
    login_initialization_info = plsdk_auth.device_user_login_initiate()

    # 2. Display necessary instructions to the user.
    #
    #    "verification_uri" and "user_code" are required under RFC 8628.
    #    "verification_uri_complete" is optional under the RFC.
    #
    #    If the user is expected to type in the URL, verification_uri will be
    #    shorter.  If the URL may be presented in a clickable means (such as a
    #    link, button, or QR code) the verification_uri_complete may offer a
    #    better user experience.
    verification_uri_complete = login_initialization_info.get(
        "verification_uri_complete")
    verification_uri = login_initialization_info.get("verification_uri")
    user_code = login_initialization_info.get("user_code")

    print("Please activate your client.")
    if verification_uri_complete:
        print(f"Visit the activation site:\n"
              f"\n\t{verification_uri_complete}\n"
              f"\nand confirm the authorization code:\n"
              f"\n\t{user_code}\n")
    else:
        print(f"Visit the activation site:\n"
              f"\n\t{verification_uri}\n"
              f"\nand enter the authorization code:\n"
              f"\n\t{user_code}\n")

    # 3. Return control to the SDK.  This will block until the user
    #    completes login.
    plsdk_auth.device_user_login_complete(login_initialization_info)


def example_main():
    # Create an auth context with a client ID that
    # is unique to this application.
    plsdk_auth = planet.Auth.from_oauth_user_device_code(
        client_id="__MUST_BE_APP_DEVELOPER_SUPPLIED__",
        requested_scopes=[
            # Request access to Planet APIs
            planet.PlanetOAuthScopes.PLANET,
            # Request a refresh token so repeated browser logins are not required
            planet.PlanetOAuthScopes.OFFLINE_ACCESS,
        ],
        save_state_to_storage=False,
    )

    # An application with no persistent storage must initialize a login every
    # time.  This is not smooth user experience.
    initialize_user_session(plsdk_auth)

    # Create a Planet SDK object that uses the loaded auth session.
    sess = planet.Session(plsdk_auth)
    pl = planet.Planet(sess)

    # Use the SDK to call Planet APIs.
    # Refreshing access tokens will be managed automatically by the SDK.
    for item in pl.data.list_searches():
        print(json.dumps(item, indent=2, sort_keys=True))


if __name__ == '__main__':
    example_main()
