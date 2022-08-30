Background Publishing Technical Reference
#########################################

Overview
********

tk-multi-bg-publish is a customizable Toolkit App that allows artists to perform ShotGrid publishes in a background process on their workstation so that they can move on to the next Task within their DCC.

It is complementary to `tk-multi-publish2`_

.. _tk-multi-publish2: https://developer.shotgridsoftware.com/tk-multi-publish2/

.. important::
    This app is meant to allow for two things to happen at once on a single workstation, it is not intended to be an all-encompassing solution for queue management.

.. important::
    You will probably use twice as many resources on your workstation!

    RAM and CPU core usage may introduce performance issues while publishes are being performed in the background on your system.

.. toctree::
    :maxdepth: 3

    works_with_publish2
    add_to_config

Sections remaining to include in this documentation (WIP)
*********************************************************

* How to add this to your config
* How to write a hook to use this app
* The Monitor interface
* The log folders

Default configuration behaviour
===============================

Background Publishing setting - True or False

Cross-reference class

def example_method(self, publisher_class):
    """

    :param publisher_class: Publish2 PostPhase
    :type PostPhaseHook: :class:`~tk_multi_publish2.base_hooks.PostPhaseHook`

    """

https://developer.shotgridsoftware.com/tk-multi-publish2/customizing.html#post-phase-hook
