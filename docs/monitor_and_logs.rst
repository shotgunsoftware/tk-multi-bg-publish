Monitor UI and logs
===================

See the user documentation available here_

----

.. _here: https://help-staging.autodesk.com/view/ALIAS/2023/ENU/?guid=Alias_ShotGrid_Workflows_alias_shotgrid_publishing_html#Background%20publishing

..
    #TODO: Need to remove the Open Log Folder comment in page above
    #TODO: See TODO comments in index.rst file

The logs are created in a different location than other ShotGrid Desktop Logs and they will not be deleted by default, you can find them here:

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
