# Copyright 2022 Planet Labs, PBC.
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
"""CLI options"""
import click

limit = click.option(
    '--limit',
    type=int,
    default=100,
    show_default=True,
    help="""Maximum number of results to return. When set to 0, no maximum is
        applied.""")  # type: ignore

pretty = click.option('--pretty', is_flag=True,
                      help='Format JSON output.')  # type: ignore
