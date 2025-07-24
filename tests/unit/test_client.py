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
"""Tests for the synchronous Planet client."""

from planet.sync import Planet


class TestPlanetSyncClient:
    """Test cases for the Planet synchronous client."""

    def test_planet_default_initialization(self):
        """Test that Planet client initializes correctly with defaults."""
        pl = Planet()

        assert pl.data is not None
        assert pl.data._client._base_url == "https://api.planet.com/data/v1"

        assert pl.orders is not None
        assert pl.orders._client._base_url == "https://api.planet.com/compute/ops"

        assert pl.subscriptions is not None
        assert pl.subscriptions._client._base_url == "https://api.planet.com/subscriptions/v1"

        assert pl.features is not None
        assert pl.features._client._base_url == "https://api.planet.com/features/v1/ogc/my"

    def test_planet_custom_base_url_initialization(self):
        """Test that Planet client accepts custom base URL."""
        pl = Planet(base_url="https://custom.planet.com")

        assert pl.data is not None
        assert pl.data._client._base_url == "https://custom.planet.com/data/v1"

        assert pl.orders is not None
        assert pl.orders._client._base_url == "https://custom.planet.com/compute/ops"

        assert pl.subscriptions is not None
        assert pl.subscriptions._client._base_url == "https://custom.planet.com/subscriptions/v1"

        assert pl.features is not None
        assert pl.features._client._base_url == "https://custom.planet.com/features/v1/ogc/my"
