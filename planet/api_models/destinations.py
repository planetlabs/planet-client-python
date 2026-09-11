# flake8: noqa
# fmt: off
# Generated code — do not edit manually.
# Reformatting this file will break `nox -s validate_models`.
# To regenerate, run:
#   nox -s generate_models

from __future__ import annotations

from enum import Enum
from typing import Annotated

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, RootModel


class AmazonS3Params(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    aws_access_key_id: Annotated[
        str, Field(description='AWS access key ID for authentication with Amazon S3.')
    ]
    aws_region: Annotated[
        str, Field(description='The AWS region where the S3 bucket is located.')
    ]
    aws_secret_access_key: Annotated[
        str,
        Field(description='AWS secret access key for authentication with Amazon S3.'),
    ]
    bucket: Annotated[
        str,
        Field(
            description='The name of the Amazon S3 bucket where data will be delivered.'
        ),
    ]
    explicit_sse: Annotated[
        bool,
        Field(description='Enable explicit server-side encryption headers for SSE-S3.'),
    ] = False


class AmazonS3PatchParams(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    aws_access_key_id: Annotated[
        str, Field(description='AWS access key ID for authentication with Amazon S3.')
    ]
    aws_secret_access_key: Annotated[
        str,
        Field(description='AWS secret access key for authentication with Amazon S3.'),
    ]
    explicit_sse: Annotated[
        bool,
        Field(description='Enable explicit server-side encryption headers for SSE-S3.'),
    ] = False


class AzureCloudStorageParams(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    account: Annotated[
        str,
        Field(
            description='The name of the Azure Storage account where data will be delivered.'
        ),
    ]
    container: Annotated[
        str,
        Field(
            description='The name of the Azure Blob Storage container within the account.'
        ),
    ]
    sas_token: Annotated[
        str,
        Field(
            description='Shared Access Signature (SAS) token for authentication with Azure Storage.'
        ),
    ]
    storage_endpoint_suffix: Annotated[
        str | None,
        Field(
            description='The storage endpoint suffix for the Azure Storage service (optional).'
        ),
    ] = None


class AzureCloudStoragePatchParams(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    sas_token: Annotated[
        str,
        Field(
            description='Shared Access Signature (SAS) token for authentication with Azure Storage.'
        ),
    ]


class DefaultDestinationRequest(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    destination_id: Annotated[
        str, Field(description='The ID of the default destination.')
    ]


class DestinationType(Enum):
    google_cloud_storage = 'google_cloud_storage'
    amazon_s3 = 'amazon_s3'
    azure_blob_storage = 'azure_blob_storage'
    oracle_cloud_storage = 'oracle_cloud_storage'
    s3_compatible = 's3_compatible'


class Error(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    code: int
    message: str


class GoogleCloudStorageParams(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    bucket: Annotated[
        str,
        Field(
            description='The name of the Google Cloud Storage bucket where data will be delivered.'
        ),
    ]
    credentials: Annotated[
        str,
        Field(
            description="Base64-encoded service account JSON credentials for Google Cloud Storage access.\n\nTo encode the credentials: `cat service-account.json | base64 | tr -d '\\n'`\n"
        ),
    ]


class GoogleCloudStoragePatchParams(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    credentials: Annotated[
        str,
        Field(
            description="Base64-encoded service account JSON credentials for Google Cloud Storage access.\n\nTo encode the credentials: `cat service-account.json | base64 | tr -d '\\n'`\n"
        ),
    ]


class Links(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    field_self: Annotated[
        str,
        Field(
            alias='_self',
            description='RFC 3986 URI representing the location of this object.',
        ),
    ]


class OracleCloudStorageParams(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    bucket: Annotated[
        str,
        Field(
            description='The name of the Oracle Cloud Storage bucket where data will be delivered.'
        ),
    ]
    customer_access_key_id: Annotated[
        str,
        Field(
            description='Customer access key ID for authentication with Oracle Cloud Storage.'
        ),
    ]
    customer_secret_key: Annotated[
        str,
        Field(
            description='Customer secret key for authentication with Oracle Cloud Storage.'
        ),
    ]
    namespace: Annotated[
        str,
        Field(
            description='The Oracle Object Storage namespace that contains the bucket.'
        ),
    ]
    region: Annotated[
        str, Field(description='The Oracle Cloud region where the bucket is located.')
    ]


class OracleCloudStoragePatchParams(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    customer_access_key_id: Annotated[
        str,
        Field(
            description='Customer access key ID for authentication with Oracle Cloud Storage.'
        ),
    ]
    customer_secret_key: Annotated[
        str,
        Field(
            description='Customer secret key for authentication with Oracle Cloud Storage.'
        ),
    ]


class Ownership(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    is_owner: Annotated[
        bool, Field(description='True if the user is the creator of the destination.')
    ]
    owner_id: Annotated[
        int, Field(description='The ID of the user who created the destination.')
    ]


class Permissions(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    can_write: Annotated[
        bool,
        Field(description='True if the user can write to the destination (patch).'),
    ]


class S3CompatibleParams(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    access_key_id: Annotated[
        str,
        Field(
            description='Access key ID for authentication with the S3-compatible service.'
        ),
    ]
    bucket: Annotated[
        str,
        Field(
            description='The name of the S3-compatible bucket where data will be delivered.'
        ),
    ]
    endpoint: Annotated[
        str,
        Field(description='The URL endpoint for the S3-compatible storage service.'),
    ]
    region: Annotated[
        str,
        Field(
            description='The region identifier for the S3-compatible storage service.'
        ),
    ]
    secret_access_key: Annotated[
        str,
        Field(
            description='Secret access key for authentication with the S3-compatible service.'
        ),
    ]
    use_path_style: Annotated[
        bool,
        Field(
            description='Use path-style URL addressing with the bucket name in the URL path.'
        ),
    ] = False


class S3CompatiblePatchParams(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    access_key_id: Annotated[
        str,
        Field(
            description='Access key ID for authentication with the S3-compatible service.'
        ),
    ]
    secret_access_key: Annotated[
        str,
        Field(
            description='Secret access key for authentication with the S3-compatible service.'
        ),
    ]
    use_path_style: Annotated[
        bool,
        Field(
            description='Use path-style URL addressing with the bucket name in the URL path.'
        ),
    ] = False


class DestinationParameters(
    RootModel[
        GoogleCloudStorageParams
        | AmazonS3Params
        | AzureCloudStorageParams
        | OracleCloudStorageParams
        | S3CompatibleParams
    ]
):
    root: Annotated[
        GoogleCloudStorageParams | AmazonS3Params | AzureCloudStorageParams | OracleCloudStorageParams | S3CompatibleParams,
        Field(description='Parameters for the given Destination type.'),
    ]


class DestinationPatchParameters(
    RootModel[
        GoogleCloudStoragePatchParams
        | AmazonS3PatchParams
        | AzureCloudStoragePatchParams
        | OracleCloudStoragePatchParams
        | S3CompatiblePatchParams
    ]
):
    root: Annotated[
        GoogleCloudStoragePatchParams | AmazonS3PatchParams | AzureCloudStoragePatchParams | OracleCloudStoragePatchParams | S3CompatiblePatchParams,
        Field(description='Patch parameters for the given Destination type.'),
    ]


class DestinationPatchRequest1(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    archive: Annotated[
        bool | None,
        Field(description='True to archive the destination, false to unarchive.'),
    ] = None
    name: Annotated[
        str | None,
        Field(
            description='A string to uniquely identify a Destination.',
            max_length=63,
            min_length=3,
        ),
    ] = None
    parameters: DestinationPatchParameters


class DestinationPatchRequest2(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    archive: Annotated[
        bool, Field(description='True to archive the destination, false to unarchive.')
    ]
    name: Annotated[
        str | None,
        Field(
            description='A string to uniquely identify a Destination.',
            max_length=63,
            min_length=3,
        ),
    ] = None
    parameters: DestinationPatchParameters | None = None


class DestinationPatchRequest3(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    archive: Annotated[
        bool | None,
        Field(description='True to archive the destination, false to unarchive.'),
    ] = None
    name: Annotated[
        str,
        Field(
            description='A string to uniquely identify a Destination.',
            max_length=63,
            min_length=3,
        ),
    ]
    parameters: DestinationPatchParameters | None = None


class DestinationPatchRequest(
    RootModel[
        DestinationPatchRequest1
        | DestinationPatchRequest2
        | DestinationPatchRequest3
    ]
):
    root: Annotated[
        DestinationPatchRequest1 | DestinationPatchRequest2 | DestinationPatchRequest3,
        Field(
            description='A DestinationPatchRequest is an object describing how to update a Destination.',
            title='Destination patch request',
        ),
    ]


class DestinationRequest(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    name: Annotated[
        str | None,
        Field(
            description='A name given to this Destination.', max_length=63, min_length=3
        ),
    ] = None
    parameters: DestinationParameters
    type: DestinationType


class Destination(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    field_links: Annotated[Links, Field(alias='_links')]
    archived: Annotated[
        AwareDatetime | None,
        Field(description='Timestamp when the Destination was archived.'),
    ]
    created: Annotated[
        AwareDatetime, Field(description='Timestamp when the Destination was created.')
    ]
    default: Annotated[
        bool | None,
        Field(
            description='True if this is the default destination for the organization.'
        ),
    ] = False
    id: Annotated[
        str, Field(description='A string to uniquely identify a Destination.')
    ]
    name: Annotated[str, Field(description='A name given to this Destination.')]
    ownership: Ownership
    parameters: DestinationParameters
    permissions: Permissions
    pl_ref: Annotated[
        str, Field(alias='pl:ref', description='A reference for the destination.')
    ]
    type: DestinationType
    updated: Annotated[
        AwareDatetime,
        Field(description='Timestamp when the Destination was last updated.'),
    ]


class DestinationsResponse(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    field_links: Annotated[Links, Field(alias='_links')]
    destinations: Annotated[
        list[Destination], Field(description='Array of Destinations.')
    ]
