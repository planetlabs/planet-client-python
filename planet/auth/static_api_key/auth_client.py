from planet.auth.auth_client import AuthClient, AuthClientConfig


class StaticApiKeyAuthConfig(AuthClientConfig):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class StaticApiKeyAuthClient(AuthClient):
    def __init__(self, client_config: StaticApiKeyAuthConfig):
        super().__init__(client_config)
