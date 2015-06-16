'''
Command line specific tests - the client should be completely mocked and the
focus should be on asserting any CLI logic prior to client method invocation

lower level lib/client tests go in the test_mod suite
'''
from click import ClickException
from click.testing import CliRunner
from mock import MagicMock
from planet import api
from planet import scripts


scripts.client = MagicMock(name='client', spec=api.Client)
runner = CliRunner()


def assert_success(result, output):
    assert result.exit_code == 0
    assert output == output


def assert_cli_exception(cause, expected):
    def thrower():
        raise cause
    try:
        scripts.call_and_wrap(thrower)
        assert False, 'did not throw'
    except ClickException, ex:
        assert ex.message == expected


def test_exception_translation():
    assert_cli_exception(api.BadQuery('bogus'), 'BadQuery: bogus')
    assert_cli_exception(api.APIException('911: alert'),
                         "Unexpected response: 911: alert")


def test_list_all_scene_types():
    retval = 'list_all_scene_types ran'
    response = MagicMock(spec=api.JSON)
    response.get_raw.return_value = retval
    scripts.client.list_all_scene_types.return_value = response
    result = runner.invoke(scripts.cli, ['list_all_scene_types'])
    assert_success(result, retval)
