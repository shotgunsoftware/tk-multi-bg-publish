# Copyright (c) 2022 Autodesk, Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.

import uuid

import sgtk
from sgtk.platform.qt import QtGui, QtCore
from tank_vendor import yaml

from . import constants

delegates = sgtk.platform.import_framework("tk-framework-qtwidgets", "delegates")
ViewItemRolesMixin = delegates.ViewItemRolesMixin


class PublishTreeModel(QtGui.QStandardItemModel, ViewItemRolesMixin):
    """
    """

    _BASE_ROLE = QtCore.Qt.UserRole + 32
    (
        STATUS_ROLE,
        ICON_ROLE,
        ICON_SIZE_ROLE,
        PROGRESS_ROLE,
        TEXT_ROLE,
        ITEM_TYPE_ROLE,
        TOOLTIP_ROLE,
        NEXT_AVAILABLE_ROLE
    ) = range(_BASE_ROLE, _BASE_ROLE + 8)

    (
        PUBLISH_SESSION,
        PUBLISH_ITEM,
        PUBLISH_TASK
    ) = range(3)

    TOOLTIP_TEXT = {
        constants.WAITING_TO_START: "The publish job is waiting to start",
        constants.PUBLISH_IN_PROGRESS: "The publish step is in progress",
        constants.PUBLISH_FINISHED: "The publish step is finished and the finalize step is waiting to start",
        constants.PUBLISH_FAILED: "The publish step has failed",
        constants.FINALIZE_IN_PROGRESS: "The finalize step is in progress",
        constants.FINALIZE_FINISHED: "The finalize step is finished",
        constants.FINALIZE_FAILED: "The finalize step has failed",
        constants.WARNING: "Something unexpected happened",
    }

    class PublishTreeItem(QtGui.QStandardItem):
        """
        """

        def __init__(self, item_type, name, session_uuid, item_uuid=None, status=None):
            """
            """

            self.__item_type = item_type
            self.__item_uuid = item_uuid
            self.__session_uuid = session_uuid

            super(PublishTreeModel.PublishTreeItem, self).__init__(name)

            if status:
                self.setData(status, PublishTreeModel.STATUS_ROLE)

        @property
        def item_type(self):
            return self.__item_type

        @property
        def item_uuid(self):
            return self.__item_uuid

        @property
        def session_uuid(self):
            return self.__session_uuid

        def data(self, role):
            """
            Override the :class:`sgtk.platform.qt.QtGui.QStandardItem` method.
            Return the data for the item for the specified role.

            :param role: The :class:`sgtk.platform.qt.QtCore.Qt.ItemDataRole` role.
            :return: The data for the specified role.
            """

            if role == PublishTreeModel.VIEW_ITEM_SEPARATOR_ROLE:
                if self.__item_type == PublishTreeModel.PUBLISH_SESSION:
                    return True
                return False

            if role == PublishTreeModel.VIEW_ITEM_HEIGHT_ROLE:
                if self.__item_type == PublishTreeModel.PUBLISH_SESSION:
                    return 50
                return -1

            if role == PublishTreeModel.PROGRESS_ROLE:
                if self.__item_type != PublishTreeModel.PUBLISH_SESSION:
                    return None
                return self.model().get_progress_value(self.__session_uuid)

            if role == PublishTreeModel.ICON_SIZE_ROLE:
                if self.__item_type == PublishTreeModel.PUBLISH_SESSION:
                    return QtCore.QSize(30, 30)
                return QtCore.QSize(18, 18)

            if role == PublishTreeModel.ITEM_TYPE_ROLE:
                return self.__item_type

            if role == PublishTreeModel.TOOLTIP_ROLE:
                if self.__item_type == PublishTreeModel.PUBLISH_TASK:
                    return PublishTreeModel.TOOLTIP_TEXT.get(self.data(PublishTreeModel.STATUS_ROLE), None)
                return None

            return super(PublishTreeModel.PublishTreeItem, self).data(role)

    def __init__(self, parent):
        """
        Class constructor.

        :param parent: The parent widget
        """

        QtGui.QStandardItemModel.__init__(self, parent)

        self.__tasks = []

        self._bundle = sgtk.platform.current_bundle()

        # Add additional roles defined by the ViewItemRolesMixin class.
        self.NEXT_AVAILABLE_ROLE = self.initialize_roles(self.NEXT_AVAILABLE_ROLE)

    def clear(self):
        """
        """

        # be sure to remove all the stored items
        self.__tasks = []

        super(PublishTreeModel, self).clear()

    def add_publish_tree(self, tree_file):
        """
        :param tree_file:
        :return:
        """

        # create an uuid for the current session. It will be useful to gather all the tasks belonging to the same
        # session
        session_uuid = uuid.uuid4()

        # load the monitor data
        with open(tree_file, "r") as fp:
            monitor_data = yaml.load(fp, Loader=yaml.FullLoader)

        # first, add an item to represent the current session
        session_item = PublishTreeModel.PublishTreeItem(
            PublishTreeModel.PUBLISH_SESSION,
            monitor_data["session_name"],
            session_uuid
        )
        self.invisibleRootItem().appendRow(session_item)

        # then, add the items and tasks
        for item in monitor_data["items"]:
            # if the parent item is the root item, do not add the item, only the task
            if item["is_parent_root"]:
                parent_item = session_item
            else:
                parent_item = PublishTreeModel.PublishTreeItem(
                    PublishTreeModel.PUBLISH_ITEM,
                    item["name"],
                    session_uuid,
                    item_uuid=item["uuid"],
                )
                session_item.appendRow(parent_item)
            for task in item["tasks"]:
                task_item = PublishTreeModel.PublishTreeItem(
                    PublishTreeModel.PUBLISH_TASK,
                    task["name"],
                    session_uuid,
                    item_uuid=task["uuid"],
                    status=task["status"],
                )
                parent_item.appendRow(task_item)
                self.__tasks.append(task_item)

    def update_publish_tree(self, tree_file):
        """
        :param tree_file:
        :return:
        """

        with open(tree_file, "r") as fp:
            monitor_data = yaml.load(fp, Loader=yaml.FullLoader)

        for item in monitor_data["items"]:
            for task in item["tasks"]:
                task_item = self.get_item_from_uuid(task["uuid"])
                if task_item:
                    task_item.setData(task["status"], PublishTreeModel.STATUS_ROLE)

    def get_item_from_uuid(self, item_uuid):
        """
        :param item_uuid:
        :return:
        """
        for i in self.__tasks:
            if i.item_uuid == item_uuid:
                return i
        return None

    def get_progress_value(self, session_uuid):
        """
        :return:
        """

        task_completed = 0
        task_nb = 0

        for t in self.__tasks:
            if t.session_uuid != session_uuid:
                continue
            task_nb += 1
            task_status = t.data(self.STATUS_ROLE)
            if task_status in [constants.PUBLISH_FINISHED, constants.FINALIZE_IN_PROGRESS]:
                task_completed += 1
            elif task_status == constants.FINALIZE_FINISHED:
                task_completed += 2

        progress = 100 * task_completed / (task_nb * 2)

        return int(progress)
