# Copyright (c) 2022 Autodesk, Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.

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
        TEXT_ROLE,
        NEXT_AVAILABLE_ROLE
    ) = range(_BASE_ROLE, _BASE_ROLE + 4)

    (
        PUBLISH_ITEM,
        PUBLISH_TASK
    ) = range(2)

    STATUS_ICONS = {
        constants.WAITING_TO_START: ":/tk-multi-batchprocess/icons/waiting_to_start.png",
        constants.PUBLISH_IN_PROGRESS: ":/tk-multi-batchprocess/icons/processing.png",
        constants.PUBLISH_FINISHED: ":/tk-multi-batchprocess/icons/processing.png",
        constants.PUBLISH_FAILED: ":/tk-multi-batchprocess/icons/failed.png",
        constants.FINALIZE_IN_PROGRESS: ":/tk-multi-batchprocess/icons/processing.png",
        constants.FINALIZE_FINISHED: ":/tk-multi-batchprocess/icons/finished.png",
        constants.FINALIZE_FAILED: ":/tk-multi-batchprocess/icons/failed.png",
        constants.WARNING: ":/tk-multi-batchprocess/icons/warning.png",
    }

    STATUS_TEXT = {
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

        def __init__(self, item_type, item_uuid, name, status):
            """
            """

            self.__item_type = item_type
            self.__item_uuid = item_uuid

            super(PublishTreeModel.PublishTreeItem, self).__init__(name)

            self.setData(status, PublishTreeModel.STATUS_ROLE)

        @property
        def item_uuid(self):
            return self.__item_uuid

        def data(self, role):
            """
            Override the :class:`sgtk.platform.qt.QtGui.QStandardItem` method.
            Return the data for the item for the specified role.

            :param role: The :class:`sgtk.platform.qt.QtCore.Qt.ItemDataRole` role.
            :return: The data for the specified role.
            """

            if role == PublishTreeModel.ICON_ROLE:
                icon_path = PublishTreeModel.STATUS_ICONS.get(self.data(PublishTreeModel.STATUS_ROLE))
                return QtGui.QIcon(icon_path)

            if role == PublishTreeModel.TEXT_ROLE:
                return PublishTreeModel.STATUS_TEXT.get(self.data(PublishTreeModel.STATUS_ROLE))

            return super(PublishTreeModel.PublishTreeItem, self).data(role)

    def __init__(self, parent):
        """
        Class constructor.

        :param parent: The parent widget
        """

        QtGui.QStandardItemModel.__init__(self, parent)

        self.__items = []

        self._bundle = sgtk.platform.current_bundle()

        # Add additional roles defined by the ViewItemRolesMixin class.
        self.NEXT_AVAILABLE_ROLE = self.initialize_roles(self.NEXT_AVAILABLE_ROLE)

    def clear(self):
        """
        """

        # be sure to remove all the stored items
        self.__items = []

        super(PublishTreeModel, self).clear()

    def add_publish_tree(self, tree_file):
        """
        :param tree_file:
        :return:
        """

        # load the publish tree
        # self._publish_manager.load(tree_file)
        with open(tree_file, "r") as fp:
            monitor_data = yaml.load(fp, Loader=yaml.FullLoader)

        for item in monitor_data["items"]:
            model_item = PublishTreeModel.PublishTreeItem(
                PublishTreeModel.PUBLISH_ITEM,
                item["uuid"],
                item["name"],
                item["status"],
            )
            for task in item["tasks"]:
                task_item = PublishTreeModel.PublishTreeItem(
                    PublishTreeModel.PUBLISH_TASK,
                    task["uuid"],
                    task["name"],
                    task["status"],
                )
                model_item.appendRow(task_item)
                self.__items.append(task_item)
            self.invisibleRootItem().appendRow(model_item)
            self.__items.append(model_item)

    def update_publish_tree(self, tree_file):
        """
        :param tree_file:
        :return:
        """

        with open(tree_file, "r") as fp:
            monitor_data = yaml.load(fp, Loader=yaml.FullLoader)

        for item in monitor_data["items"]:
            model_item = self.get_item_from_uuid(item["uuid"])
            if model_item:
                model_item.setData(item["status"], PublishTreeModel.STATUS_ROLE)
            for task in item["tasks"]:
                task_item = self.get_item_from_uuid(task["uuid"])
                if task_item:
                    task_item.setData(task["status"], PublishTreeModel.STATUS_ROLE)

    def get_item_from_uuid(self, item_uuid):
        """
        :param item_uuid:
        :return:
        """
        for i in self.__items:
            if i.item_uuid == item_uuid:
                return i
        return None
