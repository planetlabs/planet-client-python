import pytest


def pytest_addoption(parser):
    parser.addoption('--oid', help='successful order id')


@pytest.fixture
def oid(request):
    return request.config.getoption("--oid")
