#!/usr/bin/env python3
"""Simple test to verify base URL functionality works correctly."""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from planet.sync import Planet

def test_planet_base_url_configuration():
    """Test that Planet client accepts and uses custom base URLs."""
    
    # Test with custom base URLs
    custom_data_url = "https://custom-data.planet.com"
    custom_orders_url = "https://custom-orders.planet.com"
    custom_subscriptions_url = "https://custom-subscriptions.planet.com"
    custom_features_url = "https://custom-features.planet.com"
    
    # Create Planet client with custom base URLs
    pl = Planet(
        data_base_url=custom_data_url,
        orders_base_url=custom_orders_url,
        subscriptions_base_url=custom_subscriptions_url,
        features_base_url=custom_features_url
    )
    
    # Verify the base URLs are correctly set
    assert pl.data._client._base_url == custom_data_url
    assert pl.orders._client._base_url == custom_orders_url
    assert pl.subscriptions._client._base_url == custom_subscriptions_url
    assert pl.features._client._base_url == custom_features_url
    
    print("✓ All custom base URLs are correctly set")

def test_planet_default_base_urls():
    """Test that Planet client uses default base URLs when none provided."""
    
    # Create Planet client with defaults
    pl = Planet()
    
    # Verify default base URLs are used
    assert "https://api.planet.com/data/v1" in pl.data._client._base_url
    assert "https://api.planet.com/compute/ops" in pl.orders._client._base_url
    assert "https://api.planet.com/subscriptions/v1" in pl.subscriptions._client._base_url
    assert "https://api.planet.com/features/v1/ogc/my" in pl.features._client._base_url
    
    print("✓ All default base URLs are correctly set")

if __name__ == "__main__":
    test_planet_base_url_configuration()
    test_planet_default_base_urls()
    print("All tests passed! 🎉")