# Copyright 2025 Planet Labs PBC.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy of
# the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.
from planet.clients.quota import QuotaClient
from planet.sync.quota import QuotaAPI
from planet.http import Session
from planet.auth import Auth


class TestQuotaClient:
    """Test cases for the QuotaClient."""

    def test_quota_client_initialization(self):
        """Test that QuotaClient initializes correctly with default and custom URLs."""
        session = Session(auth=Auth.from_key(key="test"))
        # Test default URL
        client = QuotaClient(session)
        assert client._base_url == "https://api.planet.com/quota/v1"
        # Test custom URL
        custom_url = "https://custom.planet.com/quota/v2/"
        client_custom = QuotaClient(session, base_url=custom_url)
        assert client_custom._base_url == "https://custom.planet.com/quota/v2"

    def test_quota_client_url_methods(self):
        """Test URL construction methods."""
        session = Session(auth=Auth.from_key(key="test"))
        client = QuotaClient(session)
        assert client._reservations_url(
        ) == "https://api.planet.com/quota/v1/reservations"


class TestQuotaAPI:
    """Test cases for the synchronous QuotaAPI."""

    def test_quota_api_initialization(self):
        """Test that QuotaAPI initializes correctly."""
        session = Session(auth=Auth.from_key(key="test"))
        # Test default URL
        api = QuotaAPI(session)
        assert api._client._base_url == "https://api.planet.com/quota/v1"
        # Test custom URL
        custom_url = "https://custom.planet.com/quota/v2/"
        api_custom = QuotaAPI(session, base_url=custom_url)
        assert api_custom._client._base_url == "https://custom.planet.com/quota/v2"


class TestPlanetSyncClientQuota:
    """Test cases for quota integration in Planet sync client."""

    def test_planet_quota_initialization(self):
        """Test that Planet client includes quota API."""
        from planet.sync import Planet
        pl = Planet()
        # Test quota is included
        assert pl.quota is not None
        assert pl.quota._client._base_url == "https://api.planet.com/quota/v1"

    def test_planet_quota_custom_base_url(self):
        """Test that Planet client quota uses custom base URL."""
        from planet.sync import Planet
        pl = Planet(base_url="https://custom.planet.com")
        # Test quota uses custom URL
        assert pl.quota is not None
        assert pl.quota._client._base_url == "https://custom.planet.com/quota/v1"
