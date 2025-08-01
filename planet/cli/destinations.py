from contextlib import asynccontextmanager
import click
from click.exceptions import ClickException

from planet.cli.io import echo_json
from planet.clients.destinations import DestinationsClient

from .cmds import command
from .session import CliSession


@asynccontextmanager
async def destinations_client(ctx):
    async with CliSession() as sess:
        cl = DestinationsClient(sess, base_url=ctx.obj['BASE_URL'])
        yield cl


@click.group()  # type: ignore
@click.pass_context
@click.option('-u',
              '--base-url',
              default=None,
              help='Assign custom base Destinations API URL.')
def destinations(ctx, base_url):
    """Commands for interacting with the Destinations API"""
    ctx.obj['BASE_URL'] = base_url


async def _patch_destination(ctx, destination_id, data, pretty):
    async with destinations_client(ctx) as cl:
        try:
            response = await cl.patch_destination(destination_id, data)
            echo_json(response, pretty)
        except Exception as e:
            raise ClickException(f"Failed to patch destination: {e}")


async def _list_destinations(ctx, archived, is_owner, can_write, pretty):
    async with destinations_client(ctx) as cl:
        try:
            response = await cl.list_destinations(archived,
                                                  is_owner,
                                                  can_write)
            echo_json(response, pretty)
        except Exception as e:
            raise ClickException(f"Failed to list destinations: {e}")


async def _get_destination(ctx, destination_id, pretty):
    async with destinations_client(ctx) as cl:
        try:
            response = await cl.get_destination(destination_id)
            echo_json(response, pretty)
        except Exception as e:
            raise ClickException(f"Failed to get destination: {e}")


async def _create_destination(ctx, data, pretty):
    async with destinations_client(ctx) as cl:
        try:
            response = await cl.create_destination(data)
            echo_json(response, pretty)
        except Exception as e:
            raise ClickException(f"Failed to create destination: {e}")


@command(destinations, name="list")
@click.option('--archived',
              type=bool,
              default=None,
              help="""Set to true to include only archived destinations,
              false to exclude them.""")
@click.option('--is-owner',
              type=bool,
              default=None,
              help="""Set to true to include only destinations owned by the
              requesting user, false to exclude them.""")
@click.option(
    '--can-write',
    type=bool,
    default=None,
    help="""Set to true to include only destinations the user can modify,
    false to exclude them.""")
async def list_destinations(ctx, archived, is_owner, can_write, pretty):
    """
    List destinations with optional filters

    This command retrieves a list of destinations, with the ability to filter based on
    various attributes like archive status, ownership, and write access.

    Example:

        planet destinations list --archived false --is-owner true --can-write true
    """
    await _list_destinations(ctx, archived, is_owner, can_write, pretty)


@command(destinations, name="get")
@click.argument('destination_id')
async def get_destination(ctx, destination_id, pretty):
    """
    Retrieve a destination by ID

    This command returns detailed information about a specific destination identified
    by its `destination_id`.

    Example:

        planet destinations get my-destination-id
    """
    await _get_destination(ctx, destination_id, pretty)


@destinations.group()
def create():
    """Create a new destination."""
    pass


@command(create, name="s3")
@click.option("--bucket", required=True, help="S3 bucket name.")
@click.option("--region", required=True, help="AWS region.")
@click.option("--access-key-id", required=True, help="AWS access key ID.")
@click.option("--secret-access-key",
              required=True,
              help="AWS secret access key.")
@click.option("--explicit-sse",
              is_flag=True,
              help="Explicitly set headers for server-side encryption (SSE).")
@click.option('--name',
              help="""Optional name to assign to the destination.
              Otherwise, the bucket name is used.""")
async def create_s3(ctx,
                    bucket,
                    region,
                    access_key_id,
                    secret_access_key,
                    explicit_sse,
                    name,
                    pretty):
    """
    Create a new Amazon S3 destination.

    This command configures an S3 destination using the specified bucket name,
    AWS region, access key ID, and secret access key. You can optionally assign
    a name to the destination and enable explicit SSE-S3 server-side encryption.

    Example:

        planet destinations create s3 --bucket my-bucket --region us-west-2 --access-key-id AKIA... --secret-access-key SECRET... --name my-s3-destination
    """
    data = {
        "type": "amazon_s3",
        "parameters": {
            "bucket": bucket,
            "aws_region": region,
            "aws_access_key_id": access_key_id,
            "aws_secret_access_key": secret_access_key,
        }
    }

    if explicit_sse:
        data["parameters"]["explicit_sse"] = True
    if name:
        data["name"] = name

    await _create_destination(ctx, data, pretty)


@command(create, name="s3-compatible")
@click.option("--bucket", required=True, help="Bucket name.")
@click.option("--endpoint", required=True, help="Endpoint URL.")
@click.option("--region", required=True, help="Region.")
@click.option("--access-key-id", required=True, help="Access key ID.")
@click.option("--secret-access-key", required=True, help="Secret access key.")
@click.option("--use-path-style",
              is_flag=True,
              default=False,
              help="Use path-style addressing with bucket name in the URL.")
@click.option('--name',
              help="""Optional name to assign to the destination.
              Otherwise, the bucket name is used.""")
async def create_s3_compatible(ctx,
                               bucket,
                               endpoint,
                               region,
                               access_key_id,
                               secret_access_key,
                               use_path_style,
                               name,
                               pretty):
    """
    Create a new S3-compatible destination.

    This command configures a destination for an S3-compatible object storage service,
    using the specified bucket name, custom endpoint URL, region, and access credentials.
    You can optionally assign a name to the destination and choose whether to use
    path-style addressing.

    Example:

        planet destinations create s3-compatible --bucket my-bucket --endpoint https://objects.example.com --region us-east-1 --access-key-id AKIA... --secret-access-key SECRET... --name my-s3-comp-destination
    """
    data = {
        "type": "s3_compatible",
        "parameters": {
            "bucket": bucket,
            "endpoint": endpoint,
            "region": region,
            "access_key_id": access_key_id,
            "secret_access_key": secret_access_key,
        }
    }

    if use_path_style:
        data["parameters"]["use_path_style"] = True
    if name:
        data["name"] = name

    await _create_destination(ctx, data, pretty)


@command(create, name="ocs")
@click.option("--bucket", required=True, help="Oracle bucket name.")
@click.option("--access-key-id",
              required=True,
              help="Oracle account access key.")
@click.option("--secret-access-key",
              required=True,
              help="Oracle account secret key.")
@click.option("--namespace",
              required=True,
              help="Oracle Object Storage namespace.")
@click.option("--region",
              required=True,
              help="Oracle region bucket resides in.")
@click.option('--name',
              help="""Optional name to assign to the destination.
              Otherwise, the bucket name is used.""")
async def create_ocs(ctx,
                     bucket,
                     access_key_id,
                     secret_access_key,
                     namespace,
                     region,
                     name,
                     pretty):
    """
    Create a new Oracle Cloud Storage (OCS) destination.

    This command sets up an OCS destination using the specified bucket name, access key ID,
    secret access key, namespace, and region. You can optionally assign a name to the destination
    for easier reference.

    Example:

        planet destinations create ocs --bucket my-bucket --access-key-id OCID... --secret-access-key SECRET... --namespace my-namespace --region us-ashburn-1 --name my-ocs-destination
    """
    data = {
        "type": "oracle_cloud_storage",
        "parameters": {
            "bucket": bucket,
            "customer_access_key_id": access_key_id,
            "customer_secret_key": secret_access_key,
            "namespace": namespace,
            "region": region,
        }
    }

    if name:
        data["name"] = name

    await _create_destination(ctx, data, pretty)


@command(create, name="azure")
@click.option("--container",
              required=True,
              help="Blob storage container name.")
@click.option("--account", required=True, help="Azure account.")
@click.option("--sas-token",
              required=True,
              help="Shared-Access Signature token.")
@click.option('--storage-endpoint-suffix',
              required=False,
              help="Custom Azure Storage endpoint suffix.")
@click.option('--name',
              help="""Optional name to assign to the destination.
              Otherwise, the bucket name is used.""")
async def create_azure(ctx,
                       container,
                       account,
                       sas_token,
                       storage_endpoint_suffix,
                       name,
                       pretty):
    """
    Create a new Azure Blob Storage destination.

    This command sets up a destination in Azure Blob Storage using the specified container name,
    storage account name, and SAS token. You can optionally specify a custom endpoint suffix
    and assign a name to the destination.

    Example:

        planet destinations create azure --container my-container --account mystorage --sas-token ?sv=... --name my-azure-destination
    """

    data = {
        "type": "azure_blob_storage",
        "parameters": {
            "account": account,
            "container": container,
            "sas_token": sas_token,
        }
    }

    if storage_endpoint_suffix:
        data["parameters"]["storage_endpoint_suffix"] = storage_endpoint_suffix
    if name:
        data["name"] = name

    await _create_destination(ctx, data, pretty)


@command(create, name="gcs")
@click.option("--bucket", required=True, help="GCS bucket name.")
@click.option("--credentials",
              required=True,
              help="Base64-encoded service account credentials (JSON).")
@click.option('--name',
              help="""Optional name to assign to the destination.
              Otherwise, the bucket name is used.""")
async def create_gcs(ctx, bucket, credentials, name, pretty):
    """
    Create a new Google Cloud Storage (GCS) destination.

    This command sets up a GCS destination using the specified bucket name
    and base64-encoded service account credentials (in JSON format). You can
    optionally assign a name to the destination for easier reference.

    Note:

        The `credentials` argument must be the base64-encoded JSON of your
        Google Cloud service account key. To encode a JSON file to base64,
        you can use the following command:

            cat my_creds.json | base64 | tr -d '\n'

    Example:

        planet destinations create gcs --bucket my-bucket --credentials eyJ0eXAiOiJKV1Qi... --name my-gcs-destination
    """
    data = {
        "type": "google_cloud_storage",
        "parameters": {
            "bucket": bucket,
            "credentials": credentials,
        }
    }

    if name:
        data["name"] = name

    await _create_destination(ctx, data, pretty)


@destinations.group()
def update():
    """Update a destination."""
    pass


@command(destinations, name="archive")
@click.argument('destination_id')
async def archive(ctx, destination_id, pretty):
    """
    Archive a destination.

    This command removes the specified destination from the list endpoint without disabling it.
    Archiving a destination makes it no longer visible in the active destination list, but its
    data and configuration remain intact for potential future use.

    Example:

        planet destinations archive my-destination-id
    """
    data = {"archive": True}

    await _patch_destination(ctx, destination_id, data, pretty)


@command(destinations, name="unarchive")
@click.argument('destination_id')
async def unarchive(ctx, destination_id, pretty):
    """
    Unarchive a destination.

    This command restores a previously archived destination, making it visible again in
    the list endpoint. Unarchiving does not affect the destination's data or configuration.

    Example:

        planet destinations unarchive my-destination-id
    """
    data = {"archive": False}

    await _patch_destination(ctx, destination_id, data, pretty)


@command(destinations, name="rename")
@click.argument('destination_id')
@click.argument('name')
async def rename(ctx, destination_id, name, pretty):
    """
    Rename a destination.

    This command changes the name of the specified destination and also updates the
    `pl:ref` property, which includes the new name. The destination's data, configuration,
    and status remain intact. Only the name and its associated reference are updated.

    Example:

        planet destinations rename my-destination-id new-destination-name
    """
    data = {"name": name}

    await _patch_destination(ctx, destination_id, data, pretty)


@command(update, name="s3")
@click.argument('destination_id')
@click.option('--access-key-id', required=True, help="AWS access key ID.")
@click.option('--secret-access-key',
              required=True,
              help="AWS secret access key.")
@click.option('--explicit-sse',
              is_flag=True,
              help='Explicitly set headers for server-side encryption (SSE).')
async def update_s3(ctx,
                    destination_id,
                    access_key_id,
                    secret_access_key,
                    explicit_sse,
                    pretty):
    """
    Update S3 destination parameters.

    This command updates the parameters of an existing S3 destination, including the
    `access-key-id`, `secret-access-key`, and optionally sets headers for server-side
    encryption (SSE) using the `explicit-sse` flag. The updated parameters will be applied
    to the destination configuration without altering the destination’s other properties.

    Example:

        planet destinations update s3 my-destination-id --access-key-id NEW_ACCESS_KEY --secret-access-key NEW_SECRET_KEY
    """
    data = {
        "parameters": {
            "aws_access_key_id": access_key_id,
            "aws_secret_access_key": secret_access_key
        }
    }

    if explicit_sse:
        data["parameters"]["explicit_sse"] = True

    await _patch_destination(ctx, destination_id, data, pretty)


@command(update, name="azure")
@click.argument('destination_id')
@click.option('--sas-token', required=True, help="New SAS token.")
async def update_azure(ctx, destination_id, sas_token, pretty):
    """
    Update Azure destination parameters.

    This command updates the parameters of an existing Azure destination, specifically
    the `sas-token`. The updated SAS token will be applied to the destination configuration
    without affecting other destination properties.

    Example:

        planet destinations update azure my-destination-id --sas-token NEW_SAS_TOKEN
    """
    data = {"parameters": {"sas_token": sas_token}}

    await _patch_destination(ctx, destination_id, data, pretty)


@command(update, name="gcs")
@click.argument('destination_id')
@click.option('--credentials',
              required=True,
              help="Base64-encoded service account credentials (JSON).")
async def update_gcs(ctx, destination_id, credentials, pretty):
    """
    Update Google Cloud Storage (GCS) destination parameters.

    This command updates the credentials for an existing GCS destination. The provided
    `credentials` should be the base64-encoded JSON of the service account key. The updated
    credentials will be applied to the destination configuration without altering other properties.

    Note:

        The `credentials` argument must be the base64-encoded JSON of your Google Cloud
        service account key. To encode a JSON file to base64, you can use the following
        command:

            cat my_creds.json | base64 | tr -d '\n'

    Example:

        planet destinations update gcs my-destination-id --credentials eyJ0eXAiOiJKV1Qi...
    """
    data = {"parameters": {"credentials": credentials}}

    await _patch_destination(ctx, destination_id, data, pretty)


@command(update, name="ocs")
@click.argument('destination_id')
@click.option('--access-key-id',
              required=True,
              help="Oracle account access key.")
@click.option('--secret-access-key',
              required=True,
              help="Oracle account secret key.")
async def update_ocs(ctx,
                     destination_id,
                     access_key_id,
                     secret_access_key,
                     pretty):
    """
    Update Oracle Cloud Storage (OCS) destination parameters.

    This command updates the parameters of an existing Oracle Cloud Storage destination,
    including the `access-key-id` and `secret-access-key`. The updated credentials will
    be applied to the destination configuration without affecting other properties.

    Example:

        planet destinations update ocs my-destination-id --access-key-id NEW_ACCESS_KEY --secret-access-key NEW_SECRET_KEY
    """

    data = {
        "parameters": {
            "customer_access_key_id": access_key_id,
            "customer_secret_key": secret_access_key
        }
    }

    await _patch_destination(ctx, destination_id, data, pretty)


@command(update, name="s3-compatible")
@click.argument("destination_id")
@click.option("--access-key-id", required=True, help="Access key ID.")
@click.option("--secret-access-key", required=True, help="Secret access key.")
@click.option("--use-path-style",
              is_flag=True,
              help="Use path-style addressing with bucket name in the URL.")
async def update_s3_compatible(ctx,
                               destination_id,
                               access_key_id,
                               secret_access_key,
                               use_path_style,
                               pretty):
    """
    Update S3-compatible destination parameters.

    This command updates the parameters of an existing S3-compatible destination,
    including the `access-key-id` and `secret-access-key`. You can also optionally
    enable path-style addressing using the `--use-path-style` flag. The updated parameters
    will be applied to the destination configuration without affecting other properties.

    Example:

        planet destinations update s3-compatible my-destination-id --access-key-id NEW_ACCESS_KEY --secret-access-key NEW_SECRET_KEY
    """
    data = {
        "parameters": {
            "access_key_id": access_key_id,
            "secret_access_key": secret_access_key
        }
    }

    if use_path_style:
        data["parameters"]["use_path_style"] = True

    await _patch_destination(ctx, destination_id, data, pretty)
