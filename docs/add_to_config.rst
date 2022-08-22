Adding this app to your config
==============================

Declare the app in your ``env/includes/app_locations.yml`` file:

::

    apps.tk-multi-bg-publish.location:
      type: app_store
      name: tk-multi-bg-publish
      version: v0.1.0

::

Reference_

.. _Reference: https://github.com/shotgunsoftware/tk-config-default2/blob/72ba0043c9e5d1416ab1b6b11df34d4c90658cb6/env/includes/app_locations.yml#L83-L86

----

Tell your ``Engine`` to use the app (``env/includes/settings/tk-alias.yml``):

::

    tk-multi-bg-publish:
      location: "@apps.tk-multi-bg-publish.location"

::

Reference_

.. _Reference: https://github.com/shotgunsoftware/tk-config-default2/blob/72ba0043c9e5d1416ab1b6b11df34d4c90658cb6/env/includes/settings/tk-alias.yml#L50-L51

----

Add an additional ``collector_settings`` entry in ``env/includes/settings/tk-multi-publish2.yml``:

::

    collector_settings:
      Background Processing: True

::

Subclass the ``post_phase`` hook in the same ``env/includes/settings/tk-multi-publish2.yml`` file:

::

    post_phase: "{self}/post_phase.py:{config}/tk-multi-publish2/post_phase.py"

::

Add the ``post_phase.py`` hook to your config named  ``hooks/tk-multi-publish2/post_phase.py`` as noted above in the subclass.

You can refer to ``Alias Engine`` to see them working_ within the config_.

.. _working: https://github.com/shotgunsoftware/tk-config-default2/blob/72ba0043c9e5d1416ab1b6b11df34d4c90658cb6/env/includes/settings/tk-multi-publish2.yml#L517-L522

.. _config: https://github.com/shotgunsoftware/tk-config-default2/blob/72ba0043c9e5d1416ab1b6b11df34d4c90658cb6/env/includes/settings/tk-multi-publish2.yml#L551
