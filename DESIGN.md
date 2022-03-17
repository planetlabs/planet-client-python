# Design

## Overview

This document outlines the high-level design that informs the development of
the Planet SDK for Python.

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
