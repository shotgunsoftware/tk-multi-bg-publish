Monitor UI and logs
===================

See the user documentation available here_

----

.. _here: https://help.autodesk.com/view/SGSUB/ENU/?guid=Alias_ShotGrid_Workflows_alias_shotgrid_publishing_html#background-publishing

The logs are created in a different location than other Flow Production Tracking Logs and they will not be deleted by default, you can find them here:

``$SHOTGRID_HOME/<site name>/<config folder>/tm-bg-publish/<engine name>``

Within this folder you will find one or more temporary folder names and within each of those folders you will find three files:

.. code:: yaml

    bg_publish.log
    monitor.yml
    publish_tree.yml

These files can help you identify issues if there are any errors during the background publishing process.

Logging_

.. _Logging: https://developer.shotgridsoftware.com/tk-multi-publish2/logging.html

PublishTree_

.. _PublishTree: https://developer.shotgridsoftware.com/tk-multi-publish2/api.html#publishtree

----

You can use the `Background Publish Monitor` interface to clean up the folders and files or delete using your OS' file browser capabilities.
