# Design

This document details the design of the Planet SDK for Python.

The aspects of design this document addresses are the scope of the package,
interface principles, and implementation principles.

## Scope

The scope of this package is to provide a low-level Python API and CLI for
Planet’s services. Commands map close to 1:1 with service APIs and all service
operations are supported.


## Interface Principles

The principles of the interface design, ordered according to priority, are:
* Map the API names and endpoints as close as possible
* Synchronoize the Python API and CLI
* Adhere to command line design in:
 * Popular SDKs (aws and gcloud)
 * The geospatial toolset (gdal, rasterio)
 * GNU standards
* Support JSON in stdin/stdout


## Implementation Principles

The principles of the implementation design, in no particular order, are:

* Auto-generate as much as possible from the API specifications
* The CLI is a thin wrapper around the Python API
* Python API is asynchronous, CLI is synchronous
