How to write a hook to run in this app
======================================

Ensure your ``collector.py`` has added the `settings` for `Background Processing`:

.. code:: python

    "Background Processing": {
                "type": "bool",
                "default": False,
                "description": "Boolean to turn on/off the background publishing process.",
            },
        }

permalink_

.. _permalink: https://github.com/shotgunsoftware/tk-vred/blob/82491f025399acf0a594624bd9ad4f227bfbad07/hooks/tk-multi-publish2/basic/collector.py#L62-L67

The ``collector.py`` also needs to write the values to the `parent_item` properties:

.. code:: python

    # store the Batch Processing settings in the root item properties
    bg_processing = settings.get("Background Processing")
    if bg_processing:
        parent_item.properties["bg_processing"] = bg_processing.value

permalink2_

.. _permalink2: https://github.com/shotgunsoftware/tk-vred/blob/207efb6425fedc0b89079d68267bc82c9d659af4/hooks/tk-multi-publish2/basic/collector.py#L100-L103

----

Make sure that each ``Publish Plugin`` accesses the values in the `publish` and `finalize` methods:

.. code:: python

    # get the publish "mode" stored inside of the root item properties
    bg_processing = item.parent.properties.get("bg_processing", False)
    in_bg_process = item.parent.properties.get("in_bg_process", False)

permalink3_

.. _permalink3: https://github.com/shotgunsoftware/tk-vred/blob/82491f025399acf0a594624bd9ad4f227bfbad07/hooks/tk-multi-publish2/basic/publish_session.py#L303-L305

Example to perform your ``File Save`` only in the main Publish and not in the BG Publish:

.. code:: python

    # bump the session file to the next version
    if not bg_processing or (bg_processing and not in_bg_process):
        self._save_to_next_version(item.properties["path"], item, self.save_file)

permalink4_

.. _permalink4: https://github.com/shotgunsoftware/tk-vred/blob/82491f025399acf0a594624bd9ad4f227bfbad07/hooks/tk-multi-publish2/basic/publish_session.py#L354-L355
