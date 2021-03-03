.. THIS IS A GENERATED FILE

CLI Reference
=============


.. include:: _reference_forward.rst

Option Types Formatting
-----------------------


.. _cli-metavar-ASSET-TYPE:


ASSET-TYPE
..........


Specify Asset-Type(s) of interest. Case-insenstive,
supports glob-matching, e.g. ``visual*`` specifies ``visual`` and
``visual_xml``.


.. _cli-metavar-ITEM-TYPE:


ITEM-TYPE
.........


Specify Item-Type(s) of interest. Case-insensitive,
supports glob-matching, e.g. ``psscene*`` means ``PSScene``, ``PSScene3Band``, and
 ``PSScene4Band``. The ``all`` value specifies every Item-Type.


.. _cli-metavar-FILTER:


FILTER
......


Specify a Data API search filter provided as JSON.
``@-`` specifies stdin and ``@filename`` specifies reading from a file
named 'filename'. Otherwise, the value is assumed to be JSON.


.. _cli-metavar-GEOM:


GEOM
....


Specify a geometry in GeoJSON format either as an inline value,
stdin, or a file. ``@-`` specifies stdin and ``@filename`` specifies
reading from a file named 'filename'. Otherwise, the value is assumed to
be GeoJSON.


.. _cli-metavar-FIELD-VALUES:


FIELD VALUES...
...............


Specifies an 'in' query where FIELD is a property
of the item-type and VALUES is space or comma separated text or numbers.


.. _cli-metavar-FIELD-COMP-VALUE:


FIELD COMP VALUE...
...................


A comparison query format where FIELD is a
property of the item-type and COMP is one of lt, lte, gt, gte and VALUE is
the number or date to compare against.

Note: ISO-8601 variants are supported. For example, ``2017`` is short for
``2017-01-01T00:00:00+00:00``.


General Options
---------------


``--workers``
   The number of concurrent downloads when requesting multiple scenes. - Default 4



``--verbose``
   Specify verbosity



``--api-key``
   Valid API key - or via ENV variable PL_API_KEY



``--base-url``
   Change the base Planet API URL or ENV PL_API_BASE_URL - Default https://api.planet.com/



``--version``
   Show the version and exit.



General Commands
----------------


:ref:`cli-command-help` None



:ref:`cli-command-init` None



.. index:: help

.. _cli-command-help:


help
....


Get command help

Usage: help [OPTIONS] [COMMAND]

.. index:: init

.. _cli-command-init:


init
....


Login using email/password

Usage: init [OPTIONS]

.. list-table:: Options
   :widths: 10 80 10
   :header-rows: 1

   * - Name
     - Description

     - Format

   * - email
     - The email address associated with your Planet credentials.

     - TEXT

   * - password
     - Account password. Will not be saved.

     - TEXT

Data API
--------


:ref:`cli-command-create-search` None



:ref:`cli-command-download` None



:ref:`cli-command-filter` None



:ref:`cli-command-saved-search` None



:ref:`cli-command-search` None



:ref:`cli-command-searches` None



:ref:`cli-command-stats` None



.. index:: create-search

.. _cli-command-create-search:


create-search
.............


Create a saved search

Usage: create-search [OPTIONS]

.. list-table:: Options
   :widths: 10 80 10
   :header-rows: 1

   * - Name
     - Description

     - Format

   * - pretty
     - Format JSON output

     - BOOLEAN

   * - name
     -

     - TEXT

   * - asset-type
     - Specify asset type(s) permissions

     - :ref:`cli-metavar-asset-type`

   * - sort
     - Specify sort ordering as published/acquired asc/desc

     - FIELD ORDER...

   * - item-type
     - Specify item type(s)

     - :ref:`cli-metavar-item-type`

   * - filter-json
     - Use the specified filter

       DEFAULT: `@-`
     - :ref:`cli-metavar-filter`

   * - geom
     - Specify a geometry filter as geojson.

     - :ref:`cli-metavar-geom`

   * - string-in
     - Filter field by string in.

     - :ref:`cli-metavar-field-values`

   * - number-in
     - Filter field by numeric in.

     - :ref:`cli-metavar-field-values`

   * - range
     - Filter field by numeric range.

     - :ref:`cli-metavar-field-comp-value`

   * - date
     - Filter field by date.

     - :ref:`cli-metavar-field-comp-value`

.. index:: download

.. _cli-command-download:


download
........


Activate and download

Usage: download [OPTIONS]

.. list-table:: Options
   :widths: 10 80 10
   :header-rows: 1

   * - Name
     - Description

     - Format

   * - limit
     - Limit the number of items. Default: None

     - NUMBER

   * - dest
     - Location to download files to

       DEFAULT: `.`
     - DIRECTORY

   * - quiet
     - Disable ANSI control output

     - BOOLEAN

   * - activate-only
     - Only activate the items. Outputs URLS for downloading.

     - BOOLEAN

   * - dry-run
     - Only report the number of items that would be downloaded.

     - BOOLEAN

   * - search-id
     - Use the specified search

     - TEXT

   * - date
     - Filter field by date.

     - :ref:`cli-metavar-field-comp-value`

   * - range
     - Filter field by numeric range.

     - :ref:`cli-metavar-field-comp-value`

   * - number-in
     - Filter field by numeric in.

     - :ref:`cli-metavar-field-values`

   * - string-in
     - Filter field by string in.

     - :ref:`cli-metavar-field-values`

   * - geom
     - Specify a geometry filter as geojson.

     - :ref:`cli-metavar-geom`

   * - filter-json
     - Use the specified filter

       DEFAULT: `@-`
     - :ref:`cli-metavar-filter`

   * - item-type
     - Specify item type(s)

     - :ref:`cli-metavar-item-type`

   * - sort
     - Specify sort ordering as published/acquired asc/desc

     - FIELD ORDER...

   * - asset-type
     - Specify asset type(s)

     - :ref:`cli-metavar-asset-type`

.. index:: filter

.. _cli-command-filter:


filter
......


Output a AND filter as JSON to stdout.

If provided using --filter-json, combine the filters.

The output is suitable for use in other commands via the
--filter-json option.

Usage: filter [OPTIONS]

.. list-table:: Options
   :widths: 10 80 10
   :header-rows: 1

   * - Name
     - Description

     - Format

   * - filter-json
     - Use the specified filter

       DEFAULT: `@-`
     - :ref:`cli-metavar-filter`

   * - geom
     - Specify a geometry filter as geojson.

     - :ref:`cli-metavar-geom`

   * - string-in
     - Filter field by string in.

     - :ref:`cli-metavar-field-values`

   * - number-in
     - Filter field by numeric in.

     - :ref:`cli-metavar-field-values`

   * - range
     - Filter field by numeric range.

     - :ref:`cli-metavar-field-comp-value`

   * - date
     - Filter field by date.

     - :ref:`cli-metavar-field-comp-value`

.. index:: saved-search

.. _cli-command-saved-search:


saved-search
............


Execute a saved search

Usage: saved-search [OPTIONS] [SEARCH_ID]

.. list-table:: Options
   :widths: 10 80 10
   :header-rows: 1

   * - Name
     - Description

     - Format

   * - sort
     - Specify sort ordering as published/acquired asc/desc

     - FIELD ORDER...

   * - pretty
     - Format JSON output

     - BOOLEAN

   * - limit
     - Limit the number of items. Default: 100

       DEFAULT: `100`
     - NUMBER

.. index:: search

.. _cli-command-search:


search
......


Execute a quick search.

Usage: search [OPTIONS]

.. list-table:: Options
   :widths: 10 80 10
   :header-rows: 1

   * - Name
     - Description

     - Format

   * - limit
     - Limit the number of items. Default: 100

       DEFAULT: `100`
     - NUMBER

   * - pretty
     - Format JSON output

     - BOOLEAN

   * - asset-type
     - Specify asset type(s) permissions

     - :ref:`cli-metavar-asset-type`

   * - sort
     - Specify sort ordering as published/acquired asc/desc

     - FIELD ORDER...

   * - item-type
     - Specify item type(s)

     - :ref:`cli-metavar-item-type`

   * - filter-json
     - Use the specified filter

       DEFAULT: `@-`
     - :ref:`cli-metavar-filter`

   * - geom
     - Specify a geometry filter as geojson.

     - :ref:`cli-metavar-geom`

   * - string-in
     - Filter field by string in.

     - :ref:`cli-metavar-field-values`

   * - number-in
     - Filter field by numeric in.

     - :ref:`cli-metavar-field-values`

   * - range
     - Filter field by numeric range.

     - :ref:`cli-metavar-field-comp-value`

   * - date
     - Filter field by date.

     - :ref:`cli-metavar-field-comp-value`

.. index:: searches

.. _cli-command-searches:


searches
........


List searches

Usage: searches [OPTIONS]

.. list-table:: Options
   :widths: 10 80 10
   :header-rows: 1

   * - Name
     - Description

     - Format

   * - quick
     - Quick searches

     - BOOLEAN

   * - saved
     - Saved searches (default)

       DEFAULT: `True`
     - BOOLEAN

   * - limit
     - Limit the number of items. Default: 10

       DEFAULT: `10`
     - NUMBER

.. index:: stats

.. _cli-command-stats:


stats
.....


Get search stats

Usage: stats [OPTIONS]

.. list-table:: Options
   :widths: 10 80 10
   :header-rows: 1

   * - Name
     - Description

     - Format

   * - interval
     - Specify the interval to aggregate by.

       DEFAULT: `month`
     - [hour|day|month|week|year]

   * - date
     - Filter field by date.

     - :ref:`cli-metavar-field-comp-value`

   * - range
     - Filter field by numeric range.

     - :ref:`cli-metavar-field-comp-value`

   * - number-in
     - Filter field by numeric in.

     - :ref:`cli-metavar-field-values`

   * - string-in
     - Filter field by string in.

     - :ref:`cli-metavar-field-values`

   * - geom
     - Specify a geometry filter as geojson.

     - :ref:`cli-metavar-geom`

   * - filter-json
     - Use the specified filter

       DEFAULT: `@-`
     - :ref:`cli-metavar-filter`

   * - item-type
     - Specify item type(s)

     - :ref:`cli-metavar-item-type`

   * - sort
     - Specify sort ordering as published/acquired asc/desc

     - FIELD ORDER...

   * - asset-type
     - Specify asset type(s) permissions

     - :ref:`cli-metavar-asset-type`

   * - pretty
     - Format JSON output

     - BOOLEAN

