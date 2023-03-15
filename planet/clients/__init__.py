# Copyright 2021 Planet Labs, Inc.
# Copyright 2022 Planet Labs PBC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from .data import DataClient
from .orders import OrdersClient
from .subscriptions import SubscriptionsClient

__all__ = ['DataClient', 'OrdersClient', 'SubscriptionsClient']

# Organize client classes by their module name to allow lookup.
_client_directory = {
    'data': DataClient,
    'orders': OrdersClient,
    'subscriptions': SubscriptionsClient
}
