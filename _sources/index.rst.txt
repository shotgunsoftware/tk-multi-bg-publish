Background Publishing Technical Reference
#########################################

Overview
********

tk-multi-bg-publish is a customizable Toolkit App that allows artists to perform ShotGrid publishes in a background process on their workstation so that they can move on to the next Task within their DCC.

It is complementary to `tk-multi-publish2`_

.. _tk-multi-publish2: https://developer.shotgridsoftware.com/tk-multi-publish2/

When configured, the publish flow is updated as shown in this screen capture taken in Alias:

.. figure:: ./resources/bg_publish_flow.gif

    Screen capture of background publish flow

- The workfile will be incremented and the publish batch files will be written when you press Publish.
- The Background Monitor UI will pop to the front (if it is not open already) and you can close the main Publish UI window.
- You can then return to working in your DCC while the BG Publish is running.

Please refer to the additional user documentation available here_.

.. _here: https://help.autodesk.com/view/SGSUB/ENU/?guid=Alias_ShotGrid_Workflows_alias_shotgrid_publishing_html

..
    #TODO: Above needs to be replaced with a MURL and is currently only live on the staging site
    #TODO: Can we add a specific anchor in the docs above instead of the main Publisher section?

.. important::
    This app is meant to allow for two things to happen at once on a single workstation, it is not intended to be an all-encompassing solution for queue management.

.. important::
    You will probably use twice as many resources on your workstation!

    RAM and CPU core usage may introduce performance issues while publishes are being performed in the background on your system.

.. toctree::
    :maxdepth: 3

    works_with_publish2
    add_to_config
    how_to_write_a_hook
    monitor_and_logs
