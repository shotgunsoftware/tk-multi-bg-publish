# Copyright (c) 2022 Autodesk, Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.

import sgtk
from sgtk.platform.qt import QtGui, QtCore

from .model import PublishTreeModel
from . import constants

delegates = sgtk.platform.import_framework("tk-framework-qtwidgets", "delegates")
ViewItemDelegate = delegates.ViewItemDelegate

# colors used for the progress icons
IN_PROGRESS_COLOR = QtGui.QColor(238, 135, 38)
COMPLETED_COLOR = QtGui.QColor(14, 230, 99)
FAILED_COLOR = QtGui.QColor(187, 11, 11)
WAITING_COLOR = QtGui.QColor(255, 255, 255)


def create_publish_tree_delegate(view):
    """
    Create and return the ViewItemDelegate for the view.

    :param view: The view to create the delegate for.
    :return: The delegate for the view
    """

    # create the delegate
    delegate = ViewItemDelegate(view)

    view.setMouseTracking(True)

    # set the delegate properties
    delegate.item_padding = ViewItemDelegate.Padding(2, 7, 7, 7)
    delegate.text_padding = ViewItemDelegate.Padding(2, 7, 7, 7)
    delegate.button_margin = 0
    delegate.selection_brush = QtCore.Qt.NoBrush
    delegate.show_hover_selection = False

    # set up data roles
    delegate.text_role = QtCore.Qt.DisplayRole
    delegate.separator_role = PublishTreeModel.VIEW_ITEM_SEPARATOR_ROLE
    delegate.height_role = PublishTreeModel.VIEW_ITEM_HEIGHT_ROLE
    delegate.text_rect_valign = ViewItemDelegate.CENTER

    # add a first action to display the total progress value
    delegate.add_action(
        {
            "icon": None,  # the get_data callback will set the icon
            "show_always": True,
            "features": QtGui.QStyleOptionButton.Flat,
            "get_data": _get_progress_icon,
        },
        ViewItemDelegate.RIGHT,
    )

    # add a second action to display the status of the finalize step
    delegate.add_action(
        {
            "icon": None,  # the get_data callback will set the icon
            "show_always": True,
            "features": QtGui.QStyleOptionButton.Flat,
            "get_data": _get_finalize_icon,
        },
        ViewItemDelegate.RIGHT,
    )

    # add a third action to display the status of the publish step
    delegate.add_action(
        {
            "icon": None,  # the get_data callback will set the icon
            "show_always": True,
            "features": QtGui.QStyleOptionButton.Flat,
            "get_data": _get_publish_icon,
        },
        ViewItemDelegate.RIGHT,
    )

    return delegate


def _get_progress_icon(parent, index):
    """
    Create an icon to display the progress value for the session item.

    :param parent: This is the parent of the :class:`ViewItemDelegate`, which is the view.
    :param index: The index the action is for.
    :return: The data for the action and index.
    """

    icon = None
    tooltip = None

    # we're only displaying the progress value for the session item
    item_type = index.data(PublishTreeModel.ITEM_TYPE_ROLE)
    if item_type == PublishTreeModel.PUBLISH_SESSION:
        progress_value = index.data(PublishTreeModel.PROGRESS_ROLE)
        icon_size = index.data(PublishTreeModel.ICON_SIZE_ROLE)
        status = index.data(PublishTreeModel.STATUS_ROLE)
        text_color = (
            WAITING_COLOR
            if status not in [constants.PUBLISH_FAILED, constants.FINALIZE_FAILED]
            else FAILED_COLOR
        )
        spin_color = (
            COMPLETED_COLOR
            if status not in [constants.PUBLISH_FAILED, constants.FINALIZE_FAILED]
            else FAILED_COLOR
        )
        icon = __draw_icon(
            icon_size,
            str(progress_value),
            progress_value,
            spin_color,
            text_color=text_color,
        )
        tooltip = "Publish in progress: {}%".format(progress_value)

    return {
        "icon": icon,
        "icon_size": index.data(PublishTreeModel.ICON_SIZE_ROLE),
        "tooltip": tooltip,
        "visible": True,
    }


def _get_publish_icon(parent, index):
    """
    Create an icon to display the status of the publish step

    :param parent: This is the parent of the :class:`ViewItemDelegate`, which is the view.
    :param index: The index the action is for.
    :return: The data for the action and index.
    """

    icon = None
    tooltip = None

    # we're only displaying the progress value for the task item
    item_type = index.data(PublishTreeModel.ITEM_TYPE_ROLE)
    if item_type == PublishTreeModel.PUBLISH_TASK:

        icon_size = index.data(PublishTreeModel.ICON_SIZE_ROLE)
        status = index.data(PublishTreeModel.STATUS_ROLE)
        tooltip = index.data(PublishTreeModel.TOOLTIP_ROLE)

        if status == constants.WAITING_TO_START:
            color = WAITING_COLOR
        elif status == constants.PUBLISH_IN_PROGRESS:
            color = IN_PROGRESS_COLOR
        elif status == constants.PUBLISH_FAILED:
            color = FAILED_COLOR
        else:
            color = COMPLETED_COLOR

        icon = __draw_icon(
            icon_size, "P", 100, color, pen_size=1, font_size=6, text_color=color
        )

    return {
        "icon": icon,
        "icon_size": index.data(PublishTreeModel.ICON_SIZE_ROLE),
        "tooltip": tooltip,
        "visible": True,
    }


def _get_finalize_icon(parent, index):
    """
    Create an icon to display the status of the finalize step

    :param parent: This is the parent of the :class:`ViewItemDelegate`, which is the view.
    :param index: The index the action is for.
    :return: The data for the action and index.
    """

    icon = None
    tooltip = None

    # we're only displaying the progress value for the task item
    item_type = index.data(PublishTreeModel.ITEM_TYPE_ROLE)
    if item_type == PublishTreeModel.PUBLISH_TASK:

        icon_size = index.data(PublishTreeModel.ICON_SIZE_ROLE)
        status = index.data(PublishTreeModel.STATUS_ROLE)
        tooltip = index.data(PublishTreeModel.TOOLTIP_ROLE)

        if status == constants.FINALIZE_FAILED:
            color = FAILED_COLOR
        elif status == constants.FINALIZE_IN_PROGRESS:
            color = IN_PROGRESS_COLOR
        elif status == constants.FINALIZE_FINISHED:
            color = COMPLETED_COLOR
        else:
            color = WAITING_COLOR

        icon = __draw_icon(
            icon_size, "F", 100, color, pen_size=1, font_size=6, text_color=color
        )

    return {
        "icon": icon,
        "icon_size": index.data(PublishTreeModel.ICON_SIZE_ROLE),
        "tooltip": tooltip,
        "visible": True,
    }


def __draw_icon(
    icon_size,
    text,
    progress_value,
    progress_color,
    text_color=QtCore.Qt.white,
    pen_size=2,
    padding=2,
    font_size=10,
):
    """
    Draw a text within a circle as a QIcon to be able to use it as a progress widget by the delegate icon

    :param icon_size: Size of the icon
    :param text: Text to be used within the circle
    :param progress_value: Progress value
    :param progress_color: Color to be used to draw the circle
    :param text_color: Color to be used to draw the text
    :param pen_size: Size of the pen used to draw
    :param padding: Padding between the pixmap border and the circle
    :param font_size: Font size of the text
    :return: A QIcon containing the progress widget
    """

    # create a pixmap to store the drawing
    pixmap = QtGui.QPixmap(icon_size.width(), icon_size.height())
    pixmap.fill(QtCore.Qt.transparent)

    # initialize the painter
    painter = QtGui.QPainter(pixmap)
    painter.setRenderHint(QtGui.QPainter.Antialiasing)
    painter.setRenderHint(QtGui.QPainter.HighQualityAntialiasing)

    # draw the first arc - it will represent the percentage of the tasks already completed
    # start_angle and span_angle must be specified in 1/16th of a degree
    # zero degrees is at the 3 o’clock position
    # positive values for the angles mean counter-clockwise while negative values mean the clockwise direction
    painter.setPen(QtGui.QPen(progress_color, pen_size))
    span_angle = progress_value * 360 / 100
    start_angle = 90 * 16
    painter.drawArc(
        padding,
        padding,
        icon_size.width() - 2 * padding,
        icon_size.height() - 2 * padding,
        start_angle,
        (-16) * span_angle,
    )

    # finally, draw the text that will be displayed inside the circle
    painter.setPen(QtGui.QPen(text_color, pen_size))
    painter.setFont(QtGui.QFont("times", font_size))
    painter.drawText(
        padding * 3,
        padding * 3,
        icon_size.width() - (padding * 6),
        icon_size.height() - (padding * 6),
        QtCore.Qt.AlignCenter,
        text,
    )

    painter.end()

    return QtGui.QIcon(pixmap)
