# Design

## Overview

This document outlines the high-level design that informs the development of
the Planet SDK for Python.

## Scope

The scope of this package is to provide a low-level Python API and CLI for
Planet’s services. Commands map close to 1:1 with service APIs and all service
operations are supported.

## Principles

### Interface

The principles of the interface design, ordered according to priority, are:
* Map the API names and endpoints as close as possible
* Synchronoize the Python API and CLI
* Adhere to command line design in:
  * Popular SDKs (aws and gcloud)
  * The geospatial toolset (gdal, rasterio)
  * GNU standards
* Support JSON in stdin/stdout

### Implementation

The principles of the implementation design, in no particular order, are:

* Auto-generate as much as possible from the API specifications
* The CLI is a thin wrapper around the Python API
* Python API is asynchronous, CLI is synchronous

## Errors

### API Exceptions

Exception hierarchy:
 - Every exception inherits from the base exception, `PlanetError`.
 - All client-side exceptions are raised as `ClientError`.
 - All server-side errors are raised as specific exceptions based on the
http code. They all inherit from `APIError` and contain the unedited server
error message.

### CLI Return Codes

The following are the values and descriptions of all return codes
that can be returned at the end of running a Planet CLI command.

| Value | Description |
| ----------- | ----------- |
| 0 | Command was run successfully. |
| 1 | An error occured while the command was running. |
| 2 | Command was not run due to invalid syntax or unknown or invalid parameter.|
