# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Testing
- **Run all tests**: `nox` (runs lint, analyze, test, coverage, docs)
- **Run tests only**: `nox -s test`
- **Run tests on specific Python version**: `nox -s test-3.12`
- **Run single test file**: `nox -s test-3.12 -- tests/unit/test_http.py`
- **Run tests by keyword**: `nox -s test-3.12 -- -k test__Limiter`
- **Fast rerun (reuse environments)**: `nox -r`

### Linting and Code Quality
- **Linting**: `nox -s lint`
- **Type checking**: `nox -s analyze`
- **Code coverage**: `nox -s coverage`
- **Format code**: `yapf --in-place -r .`
- **Check formatting**: `yapf --diff -r .`

### Documentation
- **Build docs**: `nox -s docs`
- **Serve docs locally**: `nox -s watch`
- **Test documentation examples**: `nox -s docs_test`

### Example Testing
- **Test all examples**: `nox -s examples`
- **Test specific example**: `nox -s examples -- script_name.py`

### Building and Publishing
- **Build package**: `nox -s build`
- **Clean build directories**: `nox -s clean`

## Code Architecture

### High-Level Structure
The Planet SDK provides both a Python API and CLI for Planet's APIs (Data, Orders, Subscriptions, Features).

### Core Components

**API Clients** (`planet/clients/`):
- `DataClient` - Search Planet's imagery catalog
- `OrdersClient` - Process and download imagery
- `SubscriptionsClient` - Auto-process and deliver imagery
- `FeaturesClient` - Upload areas of interest

**Sync Client** (`planet/sync/`):
- `Planet` class - High-level synchronous interface combining all clients

**CLI** (`planet/cli/`):
- Entry point: `planet.cli.cli:main`
- Command modules: `data.py`, `orders.py`, `subscriptions.py`, `features.py`

**Core Infrastructure**:
- `http.py` - HTTP session management and authentication
- `auth.py` - Authentication handling
- `models.py` - Data models and response objects
- `exceptions.py` - Custom exception classes

**Request Building**:
- `data_filter.py` - Data API search filters
- `order_request.py` - Orders API request construction
- `subscription_request.py` - Subscriptions API request construction

### Key Patterns
- All API clients extend `base.py:BaseClient`
- Async and sync versions available (clients vs sync modules)
- CLI commands use Click framework with shared options in `options.py`
- Request/response validation via `specs.py` and `models.py`

## Testing Configuration
- Uses pytest with configuration in `setup.cfg`
- Supports Python 3.9-3.13
- Coverage threshold: 90% (configured in setup.cfg)
- Integration tests require Planet API credentials
- Unit tests in `tests/unit/`, integration tests in `tests/integration/`

## Code Style
- Follows PEP8 via YAPF formatter
- Type hints checked with mypy
- Flake8 linting with specific ignores (see setup.cfg)
- Docstrings in Google format for auto-generated API docs