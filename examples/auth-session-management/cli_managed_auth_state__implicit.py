import json
import logging
import planet

logging.basicConfig(level=logging.CRITICAL)


def example_main():
    # By default, the Planet SDK will be instantiated with the default auth
    # session configured by `planet auth` and saved to disk.  This default
    # initialization will also take information from environment variables.
    pl = planet.Planet()

    # Use the SDK to call Planet APIs.
    # Refreshing access tokens will be managed automatically by the SDK.
    for item in pl.data.list_searches():
        print(json.dumps(item, indent=2, sort_keys=True))


if __name__ == '__main__':
    example_main()
