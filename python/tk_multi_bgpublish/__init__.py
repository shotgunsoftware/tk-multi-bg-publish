# Copyright (c) 2022 Autodesk, Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.

# Only import constants at package load time. Dialog/UI code lives in sibling
# modules and is loaded from create_dialog/create_panel so headless engines
# (e.g. Alias bg publish with TK_ALIAS_HAS_UI=0) can init_app without Qt.
from . import constants


def _find_existing_monitor_dialog(app):
    """
    Return an already-open monitor dialog for this app, if any.

    The engine tracks Qt dialogs in ``created_qt_dialogs``; we match on a
    custom ``app_name`` property set when the dialog was first shown.

    :param app: The :class:`BackgroundPublisher` application instance.
    :returns: The existing dialog wrapper, or ``None``.
    """
    for qt_dialog in app.engine.created_qt_dialogs:
        if not hasattr(qt_dialog, "_widget"):
            continue
        app_name = qt_dialog._widget.property("app_name")
        if app_name == app.name:
            return qt_dialog
    return None


def _show_new_monitor_dialog(app, app_dialog_class):
    """
    Create and register a new monitor dialog for this app.

    :param app: The :class:`BackgroundPublisher` application instance.
    :param app_dialog_class: The widget class (typically :class:`~.dialog.AppDialog`).
    :returns: The dialog wrapper returned by the engine.
    """
    app_dialog = app.engine.show_dialog(
        app.display_name,
        app,
        app_dialog_class,
    )
    app_dialog.setProperty("app_name", app.name)
    return app_dialog


def create_dialog(app):
    """
    Show the background publish monitor as a dialog.

    Implemented here (not in app.py) so ``import_module("tk_multi_bgpublish")``
    during ``init_app`` does not pull in ``dialog`` or ``sgtk.platform.qt``.
    Matches the deferred-import pattern used by tk-multi-publish2 ``show_dialog``.

    :param app: The :class:`BackgroundPublisher` application instance.
    :returns: The widget associated with the dialog.
    """
    from .dialog import AppDialog

    app_dialog = _find_existing_monitor_dialog(app)
    if app_dialog:
        app_dialog.raise_()
        app_dialog.activateWindow()
    else:
        app_dialog = _show_new_monitor_dialog(app, AppDialog)

    return app_dialog


def create_panel(app):
    """
    Show the background publish monitor as a panel.

    Same lazy Qt loading contract as :func:`create_dialog`. Requires
    ``app._unique_panel_id`` from ``register_panel`` in ``init_app`` (UI mode only).

    :param app: The :class:`BackgroundPublisher` application instance.
    :returns: The widget associated with the panel.
    """
    from .dialog import AppDialog

    try:
        widget = app.engine.show_panel(
            app._unique_panel_id,
            app.display_name,
            app,
            AppDialog,
        )
    except AttributeError as e:
        app.logger.warning(
            "Could not execute show_panel method - please upgrade "
            "to latest core and engine! Falling back on show_dialog. "
            "Error: %s" % e
        )
        widget = create_dialog(app)

    return widget
