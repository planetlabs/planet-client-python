from contextlib import asynccontextmanager
import click
from click.exceptions import ClickException
import json
from pathlib import Path

from planet.cli.io import echo_json
from planet.clients.reports import ReportsClient

from .cmds import command
from .session import CliSession


@asynccontextmanager
async def reports_client(ctx):
    async with CliSession() as sess:
        cl = ReportsClient(sess, base_url=ctx.obj['BASE_URL'])
        yield cl


@click.group()  # type: ignore
@click.pass_context
@click.option('-u',
              '--base-url',
              default=None,
              help='Assign custom base Reports API URL.')
def reports(ctx, base_url):
    """Commands for interacting with the Reports API"""
    ctx.obj['BASE_URL'] = base_url


async def _list_reports(ctx,
                        report_type,
                        start_date,
                        end_date,
                        limit,
                        offset,
                        pretty):
    async with reports_client(ctx) as cl:
        try:
            response = await cl.list_reports(report_type=report_type,
                                             start_date=start_date,
                                             end_date=end_date,
                                             limit=limit,
                                             offset=offset)
            echo_json(response, pretty)
        except Exception as e:
            raise ClickException(f"Failed to list reports: {e}")


async def _get_report(ctx, report_id, pretty):
    async with reports_client(ctx) as cl:
        try:
            response = await cl.get_report(report_id)
            echo_json(response, pretty)
        except Exception as e:
            raise ClickException(f"Failed to get report: {e}")


async def _create_report(ctx, request_file, pretty):
    async with reports_client(ctx) as cl:
        try:
            if request_file:
                with open(request_file, 'r') as f:
                    request_data = json.load(f)
            else:
                raise ClickException("Report configuration file is required")

            response = await cl.create_report(request_data)
            echo_json(response, pretty)
        except Exception as e:
            raise ClickException(f"Failed to create report: {e}")


async def _download_report(ctx, report_id, output_file):
    async with reports_client(ctx) as cl:
        try:
            content = await cl.download_report(report_id)

            if output_file:
                output_path = Path(output_file)
                output_path.write_bytes(content)
                click.echo(f"Report downloaded to {output_path}")
            else:
                click.echo(content.decode('utf-8'))
        except Exception as e:
            raise ClickException(f"Failed to download report: {e}")


async def _get_report_status(ctx, report_id, pretty):
    async with reports_client(ctx) as cl:
        try:
            response = await cl.get_report_status(report_id)
            echo_json(response, pretty)
        except Exception as e:
            raise ClickException(f"Failed to get report status: {e}")


async def _delete_report(ctx, report_id, pretty):
    async with reports_client(ctx) as cl:
        try:
            response = await cl.delete_report(report_id)
            echo_json(response, pretty)
        except Exception as e:
            raise ClickException(f"Failed to delete report: {e}")


async def _list_report_types(ctx, pretty):
    async with reports_client(ctx) as cl:
        try:
            response = await cl.list_report_types()
            echo_json(response, pretty)
        except Exception as e:
            raise ClickException(f"Failed to list report types: {e}")


async def _get_report_export_formats(ctx, pretty):
    async with reports_client(ctx) as cl:
        try:
            response = await cl.get_report_export_formats()
            echo_json(response, pretty)
        except Exception as e:
            raise ClickException(f"Failed to get export formats: {e}")


@reports.command('list')  # type: ignore
@click.pass_context
@click.option('--type', 'report_type', help='Filter by report type')
@click.option('--start-date',
              help='Filter reports from this date (ISO 8601 format)')
@click.option('--end-date',
              help='Filter reports to this date (ISO 8601 format)')
@click.option('--limit', type=int, help='Maximum number of reports to return')
@click.option('--offset',
              type=int,
              help='Number of reports to skip for pagination')
@click.option('--pretty',
              is_flag=True,
              default=False,
              help='Format JSON output')
@command
async def list_reports_cmd(ctx,
                           report_type,
                           start_date,
                           end_date,
                           limit,
                           offset,
                           pretty):
    """List available reports"""
    await _list_reports(ctx,
                        report_type,
                        start_date,
                        end_date,
                        limit,
                        offset,
                        pretty)


@reports.command('get')  # type: ignore
@click.pass_context
@click.argument('report_id')
@click.option('--pretty',
              is_flag=True,
              default=False,
              help='Format JSON output')
@command
async def get_report_cmd(ctx, report_id, pretty):
    """Get a specific report by ID"""
    await _get_report(ctx, report_id, pretty)


@reports.command('create')  # type: ignore
@click.pass_context
@click.option('--config',
              'request_file',
              required=True,
              type=click.Path(exists=True),
              help='JSON file containing report configuration')
@click.option('--pretty',
              is_flag=True,
              default=False,
              help='Format JSON output')
@command
async def create_report_cmd(ctx, request_file, pretty):
    """Create a new report from configuration file"""
    await _create_report(ctx, request_file, pretty)


@reports.command('download')  # type: ignore
@click.pass_context
@click.argument('report_id')
@click.option(
    '--output',
    'output_file',
    type=click.Path(),
    help='Output file path. If not specified, content is printed to stdout')
@command
async def download_report_cmd(ctx, report_id, output_file):
    """Download a completed report"""
    await _download_report(ctx, report_id, output_file)


@reports.command('status')  # type: ignore
@click.pass_context
@click.argument('report_id')
@click.option('--pretty',
              is_flag=True,
              default=False,
              help='Format JSON output')
@command
async def get_report_status_cmd(ctx, report_id, pretty):
    """Get the status of a report"""
    await _get_report_status(ctx, report_id, pretty)


@reports.command('delete')  # type: ignore
@click.pass_context
@click.argument('report_id')
@click.option('--pretty',
              is_flag=True,
              default=False,
              help='Format JSON output')
@command
async def delete_report_cmd(ctx, report_id, pretty):
    """Delete a report"""
    await _delete_report(ctx, report_id, pretty)


@reports.command('types')  # type: ignore
@click.pass_context
@click.option('--pretty',
              is_flag=True,
              default=False,
              help='Format JSON output')
@command
async def list_report_types_cmd(ctx, pretty):
    """List available report types"""
    await _list_report_types(ctx, pretty)


@reports.command('formats')  # type: ignore
@click.pass_context
@click.option('--pretty',
              is_flag=True,
              default=False,
              help='Format JSON output')
@command
async def get_report_export_formats_cmd(ctx, pretty):
    """Get available export formats"""
    await _get_report_export_formats(ctx, pretty)
