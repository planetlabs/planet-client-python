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
import json
import logging

from click.testing import CliRunner

from planet.cli import cli

LOGGER = logging.getLogger(__name__)


def test_cli_collect_stdin_non_features():
    values = [{
        'key11': 'value11', 'key12': 'value12'
    }, {
        'key21': 'value21', 'key22': 'value22'
    }]

    runner = CliRunner()
    sequence = '\n'.join([json.dumps(v) for v in values])
    result = runner.invoke(cli.main, ['collect', '-'], input=sequence)

    assert result.exit_code == 0
    assert json.loads(result.output) == values


def test_cli_collect_stdin_features(feature_geojson):
    feature2 = feature_geojson.copy()
    feature2['properties'] = {'foo': 'bar'}
    values = [feature_geojson, feature2]

    runner = CliRunner()
    sequence = '\n'.join([json.dumps(v) for v in values])
    result = runner.invoke(cli.main, ['collect', '-'], input=sequence)

    assert result.exit_code == 0
    expected = {'type': 'FeatureCollection', 'features': values}
    assert json.loads(result.output) == expected


def test_cli_collect_file(feature_geojson):
    feature2 = feature_geojson.copy()
    feature2['properties'] = {'foo': 'bar'}
    values = [feature_geojson, feature2]

    runner = CliRunner()
    sequence = '\n'.join([json.dumps(v) for v in values])

    with runner.isolated_filesystem():
        with open('input.json', 'w') as f:
            f.write(sequence)

        result = runner.invoke(cli.main, ['collect', 'input.json'])

        assert result.exit_code == 0
        expected = {'type': 'FeatureCollection', 'features': values}
        assert json.loads(result.output) == expected
