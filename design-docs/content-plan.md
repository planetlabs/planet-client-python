# Content Plan Planet SDK (v2)

This document is a response to the issue #353: Quantify 'accurate and complete documentation' required for initial release. After a review of existing content, the following recommendations have been accepted as part of the V2 release. Documentation tickets will be derived from the recommendations, below.

## Overview

The list of documentation issues for this project can be found at: [https://github.com/planetlabs/planet-client-python/labels/documentation](https://github.com/planetlabs/planet-client-python/labels/documentation)


For a complete list of the project board, source, and current documentation builds, see [SDK Source & Docs in References](#SDK-Source-and-Docs).

# Planned Documentation Updates

## A note regarding location of qualification documentation:

The SDK and CLI are low-level interfaces mirroring much of the API, itself. While this documentation should make it easy for developers to use the SDK and CLI, core Planet API concepts, clarifying content, and considerations might be better located in the core API documentation on [Planet](https://developers.planet.com/docs/apis/), and then linked to from content produced here.

## SSoT

We are currently publishing documentation on [planet.com](https://developers.planet.com/docs/pythonclient/), [github.io](https://planetlabs.github.io/planet-client-python/index.html), [github wiki](https://github.com/planetlabs/planet-client-python/wiki), and on [readthedocs.com](https://planet-sdk-for-python.readthedocs.io/en/latest/). Providing a single source of truth (SSoT) ensures one definitive source of documentation, reducing the dilution of information, errors, and maintenance efforts.

### Ticket to be filed

Implement mkdocs to leverage features of readthedocs.com, but publish only on one platform. This would be planet.com unless we are making a concerted effort to recruit 3rd party contributors to the SDK, in which case, it could stay on readthedocs.com. So the publication landscape would be as follows:

* Publish the SDK V2 documentation on readthedocs.com.
* Do not mirror the SDK V2 documentation on developers.planet.com.
* End-of-life the GitHub wiki content for V2, and rely on the readme, the contributing, the changes, and the published documentation to convey information published at the wiki in 2017.
* End-of-life the github.io channel for V2, and rely on readthedocs.com as the single source of truth.

If V1 and V2 are supported at the same time, they need to be clearly demarcated, published relative to each other, and referring to each other at the page level.

Request design assets, including “open-source” design brief, or at least colors and fonts.

## Getting started experience

The SDK and CLI technical user may not have developer experience and are unfamiliar with SDKs and CLIs. A getting started experience would help them set up their environment more efficiently.

### Ticket to be filed

Provide a getting started experience that presumes the user has not used an SDK or CLI before.

Provide a relational visualization (e.g.: a dashboard of sorts) of the SDK, CLI, and API, and link to the landing page for each.

Platform overview documentation should be created on the DevCenter to explain the SDK and CLI in the context of the other Planet offerings, within the Planet platform. (This is an internal ticket on developers.planet.com, not the SDK GitHub project issues list.) The SDK should reference this overview.

## Code snippets

For the sake of this document, a code snippet is a block of code in the documentation that provides a code example of how to use the command being documented. A code snippet is not the output of the source code in the SDK. A code snippet for the SDK is not the CLI string.

### Ticket to be filed

Provide a code snippet for each call, using real-life terms (i.e., not foo & bar).

Provide a CLI cheat sheet (separate from the SDK) with examples using real-life terms. (See, for example, [The gcloud CLI cheat sheet](https://cloud.google.com/sdk/docs/cheatsheet).)

## Code samples

For the sake of this document, a code sample is a block of code that combines more than one SDK call to accomplish a task that would most likely be used in real life.

### Ticket to be filed

For every significant user story or user workflow, create a code sample. This sample could be at the bottom of each SDK section, implementing a useful group of features described above.

## Code running reference

A reference implementation is essential for creating working code snippets and samples.

### Ticket to be filed

A reference implementation of the SDK and CLI needs to be created and placed into source control.

Automated triggers should ensure the update of this implementation against the latest SDK and CLI changes.

Automated testing will prevent code from falling.

## Features list (architectural decisions & capabilities)

A new user would get context from a picture of the relationship between the core Planet API, and the SDK and the CLI.

### Ticket to be filed

Describe the architecture to the extent it’s helpful to the user, and from the user’s perspective. Explain what capabilities we’re providing in the SDK & CLI. For example:

The SDK and CLI provide low-level clients to the core Planet APIs, with a one-to-one match between function calls and API endpoints. The SDK and CLI also provide:

* Retry logic
* Some pre-validation of inputs
* Helper functions for creating JSON request arrays
* Some state management
* Managing paged responses
* Download file checksum validation

## Considerations section (like tips, but more)

Developers who are asked to implement a programmatic solution may not have experience with GIS workflows and formats. As noted above, might be better located in the core API documentation, and possibly linked from the SDK and CLI documentation. For example:

### Ticket to be filed

Add a considerations section to the documentation, either to the getting started experience or in context, that calls out useful tips and preparatory steps needed for success.

!!!note Consideration
    Orders records are kept for 90 days. After that, you'll need to work with support to retrieve older orders.

## readme.rst

The [current readme file](https://github.com/planetlabs/planet-client-python%23readme) follows industry standards and is adequate.

### Ticket to be filed

As more introductory documentation is created, it would be best to update the links in this document, with care to call out any getting started experience as well as the documentation.

A more awesome readme is possible. See a list of examples in the References section, Awesome readmes, below.

## changes.txt

The [current changes.txt](https://github.com/planetlabs/planet-client-python/blob/main/CHANGES.txt) follows industry standards and is adquate.

## contributing.md

The [current contributing.md](https://github.com/planetlabs/planet-client-python/blob/v2/CONTRIBUTING.md) file provides information about how to load the development environment. It does not provide any guidance on who might contribute or how to get involved.

This document explains how to generate a local environment and documentation, but does not provide the final locations of the builds and does not instruct on how to view the documentation.

### Ticket to be filed

Update the contributing.md file with end-to-end steps to build, change, test, and view documentation.

## GitHub wiki

The [wiki for the GitHub project](https://github.com/planetlabs/planet-client-python/wiki) has not been updated since 2017. It appears to be a getting-started guide.

### Ticket to be filed

Delete wiki content and do not use the wiki.

## Global content

Versioning, date|time stamp, licensing, privacy, security, and global navigation terms and titles should have their own review and update.

On the mkdocs version of the library:

* The versioning on the [early access V2 documentation](https://planet-sdk-for-python.readthedocs.io/en/latest/upgrading/) is wrong.
* There is no date|time stamp on the documentation releases.
* There is no copyright date on the documentation.
* There is no licensing documentation.
* There are no security & privacy links.

### Ticket to be filed

* Consider versioning a part of branding. Establish a versioning schema that works hand-in-hand with the name brand.
* Do not expose development version schemas if they confuse or contradict the brand versioning.
* Include a copyright and date|time stamp on the documentation, which can help situate the reader and provide maintenance information.
* Correct the versioning on the [early access V2 documentation](https://planet-sdk-for-python.readthedocs.io/en/latest/upgrading/) at the earliest possible time.
* Add pointers to licensing, security & privacy docs.

## Cost difference between API & SDK call
Are there any batch calls or “quick” calls that could inadvertently incur costs?

### Ticket to be filed

Call out what costs are being generated by using the SDK against the account in a considerations section.

Recommendations for batch & bulk routines.

Calls will hit the quotas, just like the APIs.

## Feedback & analytics

As this is an open source project living on GitHub, issues can be used to track user feedback.

### Ticket to be filed

Link to issues from documentation to encourage users to engage with the development team.

Consider messaging in the CLI that points to the feedback channel, such as GitHub issues and [discussions](https://docs.github.com/en/discussions).

## MkDocs plugins

Documentation components may be derived from source using MkDocs.

### Ticket to be filed

Investigate using MkDocs plugin to generate code snippets (defined above) from folder within the source or

Investigate using MkDocs plugin to derive changes.txt items.


# References
### Designs and Drafts

[design.md](https://github.com/planetlabs/planet-client-python/commit/c07afb1203d9ed0951b4cd33ef084c119f6740a9)

### Published

[Readme](https://github.com/planetlabs/planet-client-python/tree/ef8a27178d21316256ef8a5de6ee6d0758be981c%23readme)

[GitHub Wiki](https://github.com/planetlabs/planet-client-python/wiki)

[SDK Devcenter landing page](https://developers.planet.com/open/)

[planet · PyPI](https://pypi.org/project/planet/)

#### SDK Source and Docs

#### Issues & project sprints

[https://github.com/planetlabs/planet-client-python/projects/2](https://github.com/planetlabs/planet-client-python/projects/2)

[Documentation issues](https://github.com/planetlabs/planet-client-python/issues?q%3Dis%253Aissue%2Bis%253Aopen%2Blabel%253Adocumentation)

#### V2 team code source branch

[https://github.com/planetlabs/planet-client-python/](https://github.com/planetlabs/planet-client-python/)

#### Current V2 docs (erroneously tagged V1.4.9)
[https://planet-sdk-for-python.readthedocs.io/en/latest/](https://planet-sdk-for-python.readthedocs.io/en/latest)

#### Current V1.4.9 docs
[https://developers.planet.com/docs/pythonclient/](https://developers.planet.com/docs/pythonclient/)

and

[https://planetlabs.github.io/planet-client-python/index.html](https://planetlabs.github.io/planet-client-python/index.html)

#### Current V1.4.9 docs source
[https://github.com/planetlabs/planet-client-python/tree/master/docs](https://github.com/planetlabs/planet-client-python/tree/master/docs)

and

[https://github.com/planetlabs/planet-client-python//docs](https://github.com/planetlabs/planet-client-python//docs)

## GitHub flavored markdown

This document was created using [GitHub flavored markdown](https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax#GitHub-flavored-markdown)
