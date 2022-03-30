# Copyright (c) 2022 Autodesk, Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.

import sgtk
from sgtk.platform.qt import QtGui, QtCore

delegates = sgtk.platform.import_framework("tk-framework-qtwidgets", "delegates")
ViewItemDelegate = delegates.ViewItemDelegate

from .model import PublishTreeModel


def create_publish_tree_delegate(view):
    """
    :param view:
    :return:
    """

    # create the delegate
    delegate = ViewItemDelegate(view)

    view.setMouseTracking(False)

    # set the delegate properties
    delegate.text_padding = ViewItemDelegate.Padding(2, 7, 2, 7)
    delegate.selection_brush = QtCore.Qt.NoBrush
    delegate.show_hover_selection = False

    # set up data roles
    delegate.header_role = QtCore.Qt.DisplayRole
    delegate.text_role = PublishTreeModel.TEXT_ROLE

    delegate.add_action(
        {
            "icon": None, # the get_fata callback will set the icon
            "show_always": True,
            "features": QtGui.QStyleOptionButton.Flat,
            "get_data": _get_status_icon,
        },
        ViewItemDelegate.LEFT
    )

    return delegate


def _get_status_icon(parent, index):
    """
    :param parent:
    :param index:
    :return:
    """

    return {
        "icon": index.data(PublishTreeModel.ICON_ROLE),
        "visible": True
    }
