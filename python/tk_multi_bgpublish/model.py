# Copyright (c) 2022 Autodesk, Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.

import os
import uuid

import sgtk
from sgtk.platform.qt import QtGui, QtCore
from tank_vendor import yaml

from . import constants

delegates = sgtk.platform.import_framework("tk-framework-qtwidgets", "delegates")
ViewItemRolesMixin = delegates.ViewItemRolesMixin


class PublishTreeModel(QtGui.QStandardItemModel, ViewItemRolesMixin):
    """
    A model to manage publish session and tasks
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
        LOG_FOLDER_ROLE,
        NEXT_AVAILABLE_ROLE
    ) = range(_BASE_ROLE, _BASE_ROLE + 9)

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
        An item for publish element (session, item and task)
        """

        def __init__(self, item_type, name, session_uuid, log_folder, item_uuid=None):
            """
            Class constructor

            :param item_type: Type of the item (PUBLISH_SESSION, PUBLISH_ITEM or PUBLISH_TASK)
            :param name: Item name
            :param session_uuid: Unique identifier of the session the publish items and tasks belong to
            :param log_folder: Path to the folder containing all the session files (monitor file, log file, ...)
            :param item_uuid: Unique identifier of the publish item the tasks belong to
            """

            self.__item_type = item_type
            self.__item_uuid = item_uuid
            self.__session_uuid = session_uuid
            self.__log_folder = log_folder
            self.__progress_value = 0

            super(PublishTreeModel.PublishTreeItem, self).__init__(name)

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
                return self.__progress_value

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

            if role == PublishTreeModel.LOG_FOLDER_ROLE:
                return self.__log_folder

            return super(PublishTreeModel.PublishTreeItem, self).data(role)

        def setData(self, value, role):
            """
            Override teh :class:`sgtk.platform.qt.QtGui.QStandardItem` method.
            Set the data for the item and role.

            :param value: The data value to set for the item's role.
            :param role: The :class:`sgtk.platform.qt.QtCore.Qt.ItemDataRole` role.
            """

            if role == PublishTreeModel.PROGRESS_ROLE:
                self.__progress_value = value
            else:
                super(PublishTreeModel.PublishTreeItem, self).setData(value, role)

    def __init__(self, parent):
        """
        Class constructor.

        :param parent: The parent widget
        """

        QtGui.QStandardItemModel.__init__(self, parent)

        # this will be used to store all the tasks because of performance issue (going through the tree model is slower
        # than parsing a list)
        self.__tasks = []

        self._bundle = sgtk.platform.current_bundle()

        # Add additional roles defined by the ViewItemRolesMixin class.
        self.NEXT_AVAILABLE_ROLE = self.initialize_roles(self.NEXT_AVAILABLE_ROLE)

    def clear(self):
        """
        Clear the model data
        """

        self._bundle.logger.debug("Clearing the model...")

        # be sure to remove all the stored items
        self.__tasks = []

        super(PublishTreeModel, self).clear()

    def add_publish_tree(self, tree_file):
        """
        Add a new publish session to the model

        :param tree_file: Path to the file where the publish monitor data are stored
        """

        self._bundle.logger.debug("Adding a new publish session to the model...")

        # create an uuid for the current session. It will be useful to gather all the tasks belonging to the same
        # session
        session_uuid = uuid.uuid4()

        # load the monitor data
        log_folder = os.path.dirname(tree_file)
        with open(tree_file, "r") as fp:
            monitor_data = yaml.load(fp, Loader=yaml.FullLoader)

        # first, add an item to represent the current session
        session_item = PublishTreeModel.PublishTreeItem(
            PublishTreeModel.PUBLISH_SESSION,
            monitor_data["session_name"],
            session_uuid,
            log_folder
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
                    log_folder,
                    item_uuid=item["uuid"],
                )
                session_item.appendRow(parent_item)
            for task in item["tasks"]:
                task_item = PublishTreeModel.PublishTreeItem(
                    PublishTreeModel.PUBLISH_TASK,
                    task["name"],
                    session_uuid,
                    log_folder,
                    item_uuid=task["uuid"],
                )
                task_item.setData(task["status"], PublishTreeModel.STATUS_ROLE)
                parent_item.appendRow(task_item)
                self.__tasks.append(task_item)

        progress_value = self.get_progress_value(session_uuid)
        session_item.setData(progress_value, PublishTreeModel.PROGRESS_ROLE)

    def update_publish_tree(self, tree_file):
        """
        Update the publish session data

        :param tree_file: Path to the file where the publish monitor data are stored
        """

        with open(tree_file, "r") as fp:
            monitor_data = yaml.load(fp, Loader=yaml.FullLoader)

        for item in monitor_data["items"]:
            for task in item["tasks"]:
                task_item = self.get_item_from_uuid(task["uuid"])
                if task_item:

                    task_item.setData(task["status"], PublishTreeModel.STATUS_ROLE)

                    # once the task status has been updated, force the publish session to refresh its progress value
                    progress_value = self.get_progress_value(task_item.session_uuid)
                    session_item = self.get_session_item(task_item.session_uuid)
                    session_item.setData(progress_value, PublishTreeModel.PROGRESS_ROLE)
                    session_item.emitDataChanged()

    def remove_publish_tree(self, tree_file):
        """
        Remove a publish session from the model

        :param tree_file: Path to the file where the publish monitor data are stored
        """

        log_folder = os.path.dirname(tree_file)

        for r in range(self.rowCount()):
            item = self.item(r)
            if item.data(PublishTreeModel.ITEM_TYPE_ROLE) == PublishTreeModel.PUBLISH_SESSION:
                if item.data(PublishTreeModel.LOG_FOLDER_ROLE) == log_folder:
                    self.invisibleRootItem().removeRow(r)
                    break

    def get_item_from_uuid(self, item_uuid):
        """
        Get the model item from the publish item UUID

        :param item_uuid: UUID of the publish item we want to get the associated model item
        :return: The PublishTreeModel.PublishTreeItem representing the publish item
        """
        for i in self.__tasks:
            if i.item_uuid == item_uuid:
                return i
        return None

    def get_session_item(self, session_uuid):
        """
        Get the model item from the session item UUID

        :param session_uuid: UUID of the publish session we want to get the associated model item
        :return: The PublishTreeModel.PublishTreeItem representing the publish session
        """
        for r in range(self.rowCount()):
            item = self.item(r)
            if item.data(PublishTreeModel.ITEM_TYPE_ROLE) != PublishTreeModel.PUBLISH_SESSION:
                continue
            if item.session_uuid == session_uuid:
                return item
        return None

    def get_progress_value(self, session_uuid):
        """
        Calculate the progress value of the publish session

        :param session_uuid: UUID of the publish session we want to get the progress value for
        :return: The progress value of the publish session
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

        progress = 100 * task_completed / (task_nb * 2) if task_nb != 0 else 0

        return int(progress)
