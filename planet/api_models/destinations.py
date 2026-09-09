# flake8: noqa
# fmt: off
# Generated code — do not edit manually.
# To regenerate, run:
#   nox -s generate_models
# Requires: uv tool install 'datamodel-code-generator[http]'

from enum import Enum

from typing import Annotated
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, RootModel, StringConstraints


class AmazonS3Params(BaseModel):
    model_config = ConfigDict(extra='forbid', )
    aws_access_key_id: str = Field(
        ...,
        description='AWS access key ID for authentication with Amazon S3.')
    aws_region: str = Field(
        ..., description='The AWS region where the S3 bucket is located.')
    aws_secret_access_key: str = Field(
        ...,
        description='AWS secret access key for authentication with Amazon S3.')
    bucket: str = Field(
        ...,
        description=
        'The name of the Amazon S3 bucket where data will be delivered.',
    )
    explicit_sse: bool | None = Field(
        False,
        description='Enable explicit server-side encryption headers for SSE-S3.'
    )


class AmazonS3PatchParams(BaseModel):
    model_config = ConfigDict(extra='forbid', )
    aws_access_key_id: str = Field(
        ...,
        description='AWS access key ID for authentication with Amazon S3.')
    aws_secret_access_key: str = Field(
        ...,
        description='AWS secret access key for authentication with Amazon S3.')
    explicit_sse: bool | None = Field(
        False,
        description='Enable explicit server-side encryption headers for SSE-S3.'
    )


class AzureCloudStorageParams(BaseModel):
    model_config = ConfigDict(extra='forbid', )
    account: str = Field(
        ...,
        description=
        'The name of the Azure Storage account where data will be delivered.',
    )
    container: str = Field(
        ...,
        description=
        'The name of the Azure Blob Storage container within the account.',
    )
    sas_token: str = Field(
        ...,
        description=
        'Shared Access Signature (SAS) token for authentication with Azure Storage.',
    )
    storage_endpoint_suffix: str | None = Field(
        None,
        description=
        'The storage endpoint suffix for the Azure Storage service (optional).',
    )


class AzureCloudStoragePatchParams(BaseModel):
    model_config = ConfigDict(extra='forbid', )
    sas_token: str = Field(
        ...,
        description=
        'Shared Access Signature (SAS) token for authentication with Azure Storage.',
    )


class DefaultDestinationRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', )
    destination_id: str = Field(
        ..., description='The ID of the default destination.')


class DestinationType(Enum):
    google_cloud_storage = 'google_cloud_storage'
    amazon_s3 = 'amazon_s3'
    azure_blob_storage = 'azure_blob_storage'
    oracle_cloud_storage = 'oracle_cloud_storage'
    s3_compatible = 's3_compatible'


class Error(BaseModel):
    code: int
    message: str


class GoogleCloudStorageParams(BaseModel):
    model_config = ConfigDict(extra='forbid', )
    bucket: str = Field(
        ...,
        description=
        'The name of the Google Cloud Storage bucket where data will be delivered.',
    )
    credentials: str = Field(
        ...,
        description=
        "Base64-encoded service account JSON credentials for Google Cloud Storage access.\n\nTo encode the credentials: `cat service-account.json | base64 | tr -d '\\n'`\n",
    )


class GoogleCloudStoragePatchParams(BaseModel):
    model_config = ConfigDict(extra='forbid', )
    credentials: str = Field(
        ...,
        description=
        "Base64-encoded service account JSON credentials for Google Cloud Storage access.\n\nTo encode the credentials: `cat service-account.json | base64 | tr -d '\\n'`\n",
    )


class Links(BaseModel):
    field_self: str = Field(
        ...,
        alias='_self',
        description='RFC 3986 URI representing the location of this object.',
    )


class OracleCloudStorageParams(BaseModel):
    model_config = ConfigDict(extra='forbid', )
    bucket: str = Field(
        ...,
        description=
        'The name of the Oracle Cloud Storage bucket where data will be delivered.',
    )
    customer_access_key_id: str = Field(
        ...,
        description=
        'Customer access key ID for authentication with Oracle Cloud Storage.',
    )
    customer_secret_key: str = Field(
        ...,
        description=
        'Customer secret key for authentication with Oracle Cloud Storage.',
    )
    namespace: str = Field(
        ...,
        description=
        'The Oracle Object Storage namespace that contains the bucket.')
    region: str = Field(
        ...,
        description='The Oracle Cloud region where the bucket is located.')


class OracleCloudStoragePatchParams(BaseModel):
    model_config = ConfigDict(extra='forbid', )
    customer_access_key_id: str = Field(
        ...,
        description=
        'Customer access key ID for authentication with Oracle Cloud Storage.',
    )
    customer_secret_key: str = Field(
        ...,
        description=
        'Customer secret key for authentication with Oracle Cloud Storage.',
    )


class Ownership(BaseModel):
    is_owner: bool = Field(
        ..., description='True if the user is the creator of the destination.')
    owner_id: int = Field(
        ..., description='The ID of the user who created the destination.')


class Permissions(BaseModel):
    can_write: bool = Field(
        ...,
        description='True if the user can write to the destination (patch).')


class S3CompatibleParams(BaseModel):
    model_config = ConfigDict(extra='forbid', )
    access_key_id: str = Field(
        ...,
        description=
        'Access key ID for authentication with the S3-compatible service.',
    )
    bucket: str = Field(
        ...,
        description=
        'The name of the S3-compatible bucket where data will be delivered.',
    )
    endpoint: str = Field(
        ...,
        description='The URL endpoint for the S3-compatible storage service.')
    region: str = Field(
        ...,
        description=
        'The region identifier for the S3-compatible storage service.')
    secret_access_key: str = Field(
        ...,
        description=
        'Secret access key for authentication with the S3-compatible service.',
    )
    use_path_style: bool | None = Field(
        False,
        description=
        'Use path-style URL addressing with the bucket name in the URL path.',
    )


class S3CompatiblePatchParams(BaseModel):
    model_config = ConfigDict(extra='forbid', )
    access_key_id: str = Field(
        ...,
        description=
        'Access key ID for authentication with the S3-compatible service.',
    )
    secret_access_key: str = Field(
        ...,
        description=
        'Secret access key for authentication with the S3-compatible service.',
    )
    use_path_style: bool | None = Field(
        False,
        description=
        'Use path-style URL addressing with the bucket name in the URL path.',
    )


class DestinationParameters(RootModel[GoogleCloudStorageParams
                                      | AmazonS3Params
                                      | AzureCloudStorageParams
                                      | OracleCloudStorageParams
                                      | S3CompatibleParams]):
    root: (GoogleCloudStorageParams
           | AmazonS3Params
           | AzureCloudStorageParams
           | OracleCloudStorageParams
           | S3CompatibleParams) = Field(
               ..., description='Parameters for the given Destination type.')


class DestinationPatchParameters(RootModel[GoogleCloudStoragePatchParams
                                           | AmazonS3PatchParams
                                           | AzureCloudStoragePatchParams
                                           | OracleCloudStoragePatchParams
                                           | S3CompatiblePatchParams]):
    root: (GoogleCloudStoragePatchParams
           | AmazonS3PatchParams
           | AzureCloudStoragePatchParams
           | OracleCloudStoragePatchParams
           | S3CompatiblePatchParams) = Field(
               ...,
               description='Patch parameters for the given Destination type.')


class DestinationPatchRequest1(BaseModel):
    model_config = ConfigDict(extra='forbid', )
    archive: bool | None = Field(
        None,
        description='True to archive the destination, false to unarchive.')
    name: Annotated[
        str, StringConstraints(min_length=3, max_length=63)] | None = Field(
            None, description='A string to uniquely identify a Destination.')
    parameters: DestinationPatchParameters


class DestinationPatchRequest2(BaseModel):
    model_config = ConfigDict(extra='forbid', )
    archive: bool = Field(
        ...,
        description='True to archive the destination, false to unarchive.')
    name: Annotated[
        str, StringConstraints(min_length=3, max_length=63)] | None = Field(
            None, description='A string to uniquely identify a Destination.')
    parameters: DestinationPatchParameters | None = None


class DestinationPatchRequest3(BaseModel):
    model_config = ConfigDict(extra='forbid', )
    archive: bool | None = Field(
        None,
        description='True to archive the destination, false to unarchive.')
    name: Annotated[
        str, StringConstraints(min_length=3, max_length=63)] = Field(
            ..., description='A string to uniquely identify a Destination.')
    parameters: DestinationPatchParameters | None = None


class DestinationPatchRequest(RootModel[DestinationPatchRequest1
                                        | DestinationPatchRequest2
                                        | DestinationPatchRequest3]):
    root: (
        DestinationPatchRequest1 | DestinationPatchRequest2
        | DestinationPatchRequest3
    ) = Field(
        ...,
        description=
        'A DestinationPatchRequest is an object describing how to update a Destination.',
        title='Destination patch request')


class DestinationRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', )
    name: Annotated[
        str, StringConstraints(min_length=3, max_length=63)] | None = Field(
            None, description='A name given to this Destination.')
    parameters: DestinationParameters
    type: DestinationType


class Destination(BaseModel):
    field_links: Links = Field(..., alias='_links')
    archived: AwareDatetime | None = Field(
        None, description='Timestamp when the Destination was archived.')
    created: AwareDatetime = Field(
        ..., description='Timestamp when the Destination was created.')
    default: bool | None = Field(
        None,
        description=
        'True if this is the default destination for the organization.')
    id: str = Field(...,
                    description='A string to uniquely identify a Destination.')
    name: str = Field(..., description='A name given to this Destination.')
    ownership: Ownership
    parameters: DestinationParameters
    permissions: Permissions
    pl_ref: str = Field(...,
                        alias='pl:ref',
                        description='A reference for the destination.')
    type: DestinationType
    updated: AwareDatetime = Field(
        ..., description='Timestamp when the Destination was last updated.')


class DestinationsResponse(BaseModel):
    field_links: Links = Field(..., alias='_links')
    destinations: list[Destination] = Field(
        ..., description='Array of Destinations.')
