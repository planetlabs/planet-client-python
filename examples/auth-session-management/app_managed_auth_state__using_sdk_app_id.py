import json
import planet


def example_main():
    # Load the OAuth2 user-interactive client configration that is built-into the SDK.
    # This configuration is shared with the `planet` CLI command.
    # When save_state_to_storage is true, sessions will be shared with the
    # CLI and saved to the user's home directory.  When save_state_to_storage
    # is false, the state will only be persistent in memory and the
    # user will need to login each time the application is run.
    plsdk_auth = planet.Auth.from_profile("planet-user",
                                          save_state_to_storage=False)

    if not plsdk_auth.is_initialized():
        plsdk_auth.user_login(allow_open_browser=True, allow_tty_prompt=True)

    # Create a Planet SDK object that uses the loaded auth session.
    sess = planet.Session(plsdk_auth)
    pl = planet.Planet(sess)

    # Use the SDK to call Planet APIs.
    # Refreshing access tokens will be managed automatically by the SDK.
    for item in pl.data.list_searches():
        print(json.dumps(item, indent=2, sort_keys=True))


if __name__ == "__main__":
    example_main()
