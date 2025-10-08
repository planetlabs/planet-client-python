import json
import planet


def example_main():
    # Create an auth context with a client ID that
    # is unique to this application.
    plsdk_auth = planet.Auth.from_oauth_user_auth_code(
        client_id="__MUST_BE_APP_DEVELOPER_SUPPLIED__",
        requested_scopes=[
            # Request access to Planet APIs
            planet.PlanetOAuthScopes.PLANET,
            # Request a refresh token so repeated browser logins are not required
            planet.PlanetOAuthScopes.OFFLINE_ACCESS,
        ],
        callback_url="http://localhost:8080",
        profile_name="my-name-for-example-user-session-with-local-browser",
        save_state_to_storage=True,
    )

    # In contrast to in-memory applications that must initialize a login every
    # time, an app with persistent storage can skip user prompts when they
    # are not needed.
    # This helper will prompt the user only when it is necessary.
    plsdk_auth.ensure_initialized(allow_open_browser=True, allow_tty_prompt=True)

    # Create a Planet SDK object that uses the loaded auth session.
    sess = planet.Session(plsdk_auth)
    pl = planet.Planet(sess)

    # Use the SDK to call Planet APIs.
    # Refreshing access tokens will be managed automatically by the SDK.
    for item in pl.data.list_searches():
        print(json.dumps(item, indent=2, sort_keys=True))


if __name__ == '__main__':
    example_main()
