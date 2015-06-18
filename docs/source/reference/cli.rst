.. module:: planet.scripts

.. cli:

Planet CLI
==========

This library comes with a command line interface to expose many common requests, such as searching, downloading, and obtaining metadata.

Here's an example of what can be done using the cli and GitHub Gists.

.. code-block:: bash


    # Search Planet's API for imagery acquired between June 17, 2015 and June 18, 2015
    planet search --where acquired gt 2015-06-17 --where acquired lt 2015-06-18 | gist -f planet-imagery-20150617-20150618.geojson
    
.. raw:: html

    <div style="margin-top:10px; margin-bottom:20px">
      <iframe class='ghmap' width="640" height="400" src="https://render.githubusercontent.com/view/geojson/?url=https%3A%2F%2Fgist.githubusercontent.com%2Fkapadia%2F6e722427cecd9ac79971%2Fraw%2Fhyperion-20150401-20150501.geojson#aa859151-d85a-414d-865c-9704fae891a1" frameborder="0"></iframe>
    </div>
    
    <script>
    window.onresize = function(e) {
      var mainEl = document.querySelector('#planet-cli');
      
      var mapElems = document.querySelectorAll('.ghmap');
      for (var i = 0; i < mapElems.length; i++) {
        mapElems[i].width = mainEl.clientWidth;
      }
    }
    
    window.onresize();
    </script>