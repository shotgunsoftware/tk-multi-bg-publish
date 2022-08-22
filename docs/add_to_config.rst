Adding this app to your config
==============================

Declare the app in your ``env/includes/app_locations.yml`` file:

::

    apps.tk-multi-bg-publish.location:
      type: app_store
      name: tk-multi-bg-publish
      version: v0.1.0

::

Tell your ``Engine`` to use the app (``env/includes/settings/tk-alias.yml``):

::

    tk-multi-bg-publish:
      location: "@apps.tk-multi-bg-publish.location"

::

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
