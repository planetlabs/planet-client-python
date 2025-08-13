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
"""Tests for the TaskingClient."""

import pytest
from unittest.mock import Mock

from planet.clients.tasking import TaskingClient, TaskingOrderStates
from planet import exceptions


class TestTaskingOrderStates:
    """Test TaskingOrderStates helper class."""

    def test_reached(self):
        """Test that reached correctly identifies when a state has been reached."""
        assert not TaskingOrderStates.reached('running', 'queued')
        assert TaskingOrderStates.reached('running', 'running')
        assert TaskingOrderStates.reached('running', 'success')
        assert TaskingOrderStates.reached('running', 'failed')

    def test_passed(self):
        """Test that passed correctly identifies when a state has been passed."""
        assert not TaskingOrderStates.passed('running', 'queued')
        assert not TaskingOrderStates.passed('running', 'running')
        assert TaskingOrderStates.passed('running', 'success')
        assert TaskingOrderStates.passed('running', 'failed')

    def test_is_final(self):
        """Test that is_final correctly identifies final states."""
        assert not TaskingOrderStates.is_final('queued')
        assert not TaskingOrderStates.is_final('running')
        assert TaskingOrderStates.is_final('success')
        assert TaskingOrderStates.is_final('failed')
        assert TaskingOrderStates.is_final('cancelled')


class TestTaskingClient:
    """Test TaskingClient functionality."""

    def test_check_order_id_valid(self):
        """Test that valid UUID order IDs pass validation."""
        valid_id = "550e8400-e29b-41d4-a716-446655440000"
        # Should not raise exception
        TaskingClient._check_order_id(valid_id)

    def test_check_order_id_invalid(self):
        """Test that invalid order IDs raise ClientError."""
        invalid_ids = [
            "not-a-uuid",
            "123",
            "",
            None,
            "550e8400-e29b-41d4-a716-44665544000g",  # invalid character
        ]

        for invalid_id in invalid_ids:
            with pytest.raises(exceptions.ClientError):
                TaskingClient._check_order_id(invalid_id)

    def test_init_default_base_url(self):
        """Test TaskingClient initialization with default base URL."""
        session = Mock()
        client = TaskingClient(session)
        assert client._base_url == "https://api.planet.com/tasking/v2"

    def test_init_custom_base_url(self):
        """Test TaskingClient initialization with custom base URL."""
        session = Mock()
        custom_url = "https://custom.planet.com/tasking/v2/"
        client = TaskingClient(session, base_url=custom_url)
        assert client._base_url == "https://custom.planet.com/tasking/v2"

    def test_orders_url_no_order_id(self):
        """Test _orders_url method without order ID."""
        session = Mock()
        client = TaskingClient(session)
        url = client._orders_url()
        assert url == "https://api.planet.com/tasking/v2/orders"

    def test_orders_url_with_order_id(self):
        """Test _orders_url method with order ID."""
        session = Mock()
        client = TaskingClient(session)
        order_id = "550e8400-e29b-41d4-a716-446655440000"
        url = client._orders_url(order_id)
        assert url == f"https://api.planet.com/tasking/v2/orders/{order_id}"
