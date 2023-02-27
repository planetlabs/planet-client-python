"""Session module tests."""

import pytest

from planet import DataClient, OrdersClient, SubscriptionsClient, Session
from planet.exceptions import ClientError


@pytest.mark.parametrize("client_name,client_class",
                         [('data', DataClient), ('orders', OrdersClient),
                          ('subscriptions', SubscriptionsClient)])
def test_session_get_client(client_name, client_class):
    """Get a client from a session."""
    session = Session()
    client = session.client(client_name)
    assert isinstance(client, client_class)


def test_session_get_client_error():
    """Get an exception when no such client exists."""
    session = Session()
    with pytest.raises(ClientError):
        _ = session.client('bogus')
