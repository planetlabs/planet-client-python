Planet Labs Client
==================

Client library for interfacing with the Planet Labs Public Data API. The API supports a variety of requests for searching and downloading Planet Labs metadata and imagery.

.. note:: A Planet Labs API key is required to access the API.

Installation
------------

.. code-block:: bash

    pip install planet


Examples
--------

These two example demonstrate how to access metadata for a Planet Labs scene.


Python
******

.. code-block:: python

    # Import the module
    from planet import api
    
    # Initialize a client object with a valid API key
    client = api.Client(api_key='xyz')
    
    scene_id = '20150603_183927_090b'
    
    metadata = client.get_scene_metadata(scene_id)


Command Line
************

.. code-block:: bash
    
    $ planet metadata 20150603_183927_090b
    {
      "geometry": {
        "type": "Polygon",
        "coordinates": [
          [
            [
              -143.0043622417889,
              69.3847738854277
            ],
            [
              -143.1281804378499,
              69.47744935811004
            ],
            [
              -143.52433425304486,
              69.41172917566918
            ],
            [
              -143.39939224306457,
              69.31930925533831
            ],
            [
              -143.0043622417889,
              69.3847738854277
            ]
          ]
        ]
      },
      "type": "Feature",
      "id": "20150615_190229_0905",
      ...


Contents:

.. toctree::
   :maxdepth: 2
   
   reference/cli
   reference/api


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`