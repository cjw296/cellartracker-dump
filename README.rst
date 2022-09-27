CellarTracker dumper
====================

Quick and dirty dump of all a user's data in `CellarTracker`__ to csv.

__ https://www.cellartracker.com/

Create a virtualenv using the ``requirements.txt`` file, then:

.. code-block:: bash

    python cellartracker.py login
    python cellartracker.py dump ~/Dropbox/cellartracker-dump/
