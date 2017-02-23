.. THIS IS A GENERATED FILE

CLI Reference
=============


.. include:: _reference_forward.rst

Option Types Formatting
-----------------------


.. _cli-metavar-FIELD-COMP-VALUE:


FIELD COMP VALUE...
...................


A comparison query format where FIELD is a
property of the item-type and COMP is one of lt, lte, gt, gte and VALUE is
the number or date to compare against.

ISO-8601 variants are supported. For example, `2017` is short for the full
`2017-01-01T00:00:00+00:00`.


.. _cli-metavar-FIELD-VALUES:


FIELD VALUES...
...............


Specifies an 'in' query where FIELD is a property
of the item-type and VALUES is space or comma separated text or numbers.


.. _cli-metavar-GEOM:


GEOM
....


Specify a geometry in GeoJSON format either as an inline value,
stdin, or a file. `@-` specifies stdin and `@filename` specifies reading
from a file named 'filename'. Other wise, the value is assumed to be
GeoJSON.


.. _cli-metavar-FILTER:


FILTER
......


Specify a Data API search filter provided as JSON.
`@-` specifies stdin and `@filename` specifies reading from a file named
'filename'. Other wise, the value is assumed to be JSON.


.. _cli-metavar-ITEM-TYPE:


ITEM-TYPE
.........


Specify Item-Type(s) of interest. Case-insensitive,
supports glob-matching, e.g. `psscene*` means `PSScene3Band` and
`PSScene4Band`. The `all` value specifies every Item-Type.


.. _cli-metavar-ASSET-TYPE:


ASSET-TYPE
..........


Specify Asset-Type(s) of interest. Case-insenstive,
supports glob-matching, e.g. `visual*` specifies `visual` and `visual_xml`.


General Options
---------------


``--workers``
   The number of concurrent downloads when requesting multiple scenes.



``--verbose``
   Specify verbosity



``--api_key``
   Valid API key - or via env variable PL_API_KEY



``--base_url``
   Change the base Planet API URL



``--version``
   Show the version and exit.



Commands
--------


:ref:`cli-command-create-search` Create a saved search



:ref:`cli-command-download` Activate and download



:ref:`cli-command-filter` Build a AND filter from the specified filter...



:ref:`cli-command-help` Get command help



:ref:`cli-command-init` Login using email/password



:ref:`cli-command-quick-search` Execute a quick search



:ref:`cli-command-saved-search` Execute a saved search



:ref:`cli-command-searches` List searches



:ref:`cli-command-stats` Get search stats



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

   * - item_type
     - Specify item type(s)

     - :ref:`cli-metavar-item-type`

   * - filter_json
     - Use the specified filter

       DEFAULT: `@-`
     - :ref:`cli-metavar-filter`

   * - geom
     - Specify a geometry filter as geojson. "-" for stdin or @file

     - :ref:`cli-metavar-geom`

   * - string_in
     - Filter field by string in.

     - :ref:`cli-metavar-field-values`

   * - number_in
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
     - Limit the number of items.

     - NUMBER

   * - dest
     - Location to download files to

     - PATH

   * - date
     - Filter field by date.

     - :ref:`cli-metavar-field-comp-value`

   * - range
     - Filter field by numeric range.

     - :ref:`cli-metavar-field-comp-value`

   * - number_in
     - Filter field by numeric in.

     - :ref:`cli-metavar-field-values`

   * - string_in
     - Filter field by string in.

     - :ref:`cli-metavar-field-values`

   * - geom
     - Specify a geometry filter as geojson. "-" for stdin or @file

     - :ref:`cli-metavar-geom`

   * - filter_json
     - Use the specified filter

       DEFAULT: `@-`
     - :ref:`cli-metavar-filter`

   * - item_type
     - Specify item type(s)

     - :ref:`cli-metavar-item-type`

   * - asset_type
     - Specify asset type(s)

     - :ref:`cli-metavar-asset-type`

.. index:: filter

.. _cli-command-filter:


filter
......


Build a AND filter from the specified filter options and output to
stdout

Usage: filter [OPTIONS]

.. list-table:: Options
   :widths: 10 80 10
   :header-rows: 1

   * - Name
     - Description

     - Format

   * - filter_json
     - Use the specified filter

       DEFAULT: `@-`
     - :ref:`cli-metavar-filter`

   * - geom
     - Specify a geometry filter as geojson. "-" for stdin or @file

     - :ref:`cli-metavar-geom`

   * - string_in
     - Filter field by string in.

     - :ref:`cli-metavar-field-values`

   * - number_in
     - Filter field by numeric in.

     - :ref:`cli-metavar-field-values`

   * - range
     - Filter field by numeric range.

     - :ref:`cli-metavar-field-comp-value`

   * - date
     - Filter field by date.

     - :ref:`cli-metavar-field-comp-value`

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
     - 

     - TEXT

   * - password
     - 

     - TEXT

.. index:: quick-search

.. _cli-command-quick-search:


quick-search
............


Execute a quick search

Usage: quick-search [OPTIONS]

.. list-table:: Options
   :widths: 10 80 10
   :header-rows: 1

   * - Name
     - Description

     - Format

   * - limit
     - Limit the number of items.

       DEFAULT: `100`
     - NUMBER

   * - pretty
     - Format JSON output

     - BOOLEAN

   * - item_type
     - Specify item type(s)

     - :ref:`cli-metavar-item-type`

   * - filter_json
     - Use the specified filter

       DEFAULT: `@-`
     - :ref:`cli-metavar-filter`

   * - geom
     - Specify a geometry filter as geojson. "-" for stdin or @file

     - :ref:`cli-metavar-geom`

   * - string_in
     - Filter field by string in.

     - :ref:`cli-metavar-field-values`

   * - number_in
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

     - BOOLEAN

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

   * - number_in
     - Filter field by numeric in.

     - :ref:`cli-metavar-field-values`

   * - string_in
     - Filter field by string in.

     - :ref:`cli-metavar-field-values`

   * - geom
     - Specify a geometry filter as geojson. "-" for stdin or @file

     - :ref:`cli-metavar-geom`

   * - filter_json
     - Use the specified filter

       DEFAULT: `@-`
     - :ref:`cli-metavar-filter`

   * - item_type
     - Specify item type(s)

     - :ref:`cli-metavar-item-type`

   * - pretty
     - Format JSON output

     - BOOLEAN

