import json
import planet


def example_main():
    # By default, the Planet SDK will be instantiated with the default auth
    # session configured by `planet auth` and saved to disk.  This default
    # initialization will also inspect environment variables for configuration.
    pl = planet.Planet()

    # Use the SDK to call Planet APIs.
    # Refreshing OAuth2 access tokens will be managed automatically by the SDK.
    for item in pl.data.list_searches():
        print(json.dumps(item, indent=2, sort_keys=True))


if __name__ == '__main__':
    example_main()
