# Copyright (c) 2022 Autodesk, Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.

import os
import tempfile
import time

import sgtk
from sgtk.platform.qt import QtCore, QtGui

from .ui.dialog import Ui_Dialog
from .model import PublishTreeModel
from .delegate import create_publish_tree_delegate

shotgun_globals = sgtk.platform.import_framework("tk-framework-shotgunutils", "shotgun_globals")
task_manager = sgtk.platform.import_framework("tk-framework-shotgunutils", "task_manager")
BackgroundTaskManager = task_manager.BackgroundTaskManager


class AppDialog(QtGui.QWidget):
    """
    Main application widget.
    """

    @property
    def hide_tk_title_bar(self):
        """
        Tell the system to not show the std toolbar
        """
        return True

    def __init__(self, parent=None):
        """
        Constructor
        """

        # first, call the base class and let it do its thing.
        QtGui.QWidget.__init__(self, parent)

        # this variable will be used to store all the monitor files already loaded
        self.__monitor_files = []

        self._bundle = sgtk.platform.current_bundle()
        self._cache_folder = os.path.join(
            self._bundle.cache_location, self._bundle.engine.name
        )

        # now load in the UI that was created in the UI designer
        self._ui = Ui_Dialog()
        self._ui.setupUi(self)

        self._pending_requests = []
        self._bg_task_manager = BackgroundTaskManager(self, max_threads=2)
        self._bg_task_manager.start_processing()
        shotgun_globals.register_bg_task_manager(self._bg_task_manager)

        # create the model to store all the publish information
        self._publish_tree_model = PublishTreeModel(self)
        self._ui.view.setModel(self._publish_tree_model)

        # create the delegate used to correctly the model data into the view
        self._publish_tree_delegate = create_publish_tree_delegate(self._ui.view)
        self._ui.view.setItemDelegate(self._publish_tree_delegate)

        # register some signals/slots
        self._bg_task_manager.task_completed.connect(self._on_background_task_completed)
        self._bg_task_manager.task_failed.connect(self._on_background_task_failed)

        # load the data
        task_id = self._bg_task_manager.add_task(
            self.reload
        )
        self._pending_requests.append(task_id)

    def closeEvent(self, event):
        """
        Overriden method triggered when the widget is closed.  Cleans up as much as possible
        to help the GC.

        :param event: Close event
        """

        # close down back ground tasks
        if self._bg_task_manager:
            shotgun_globals.unregister_bg_task_manager(self._bg_task_manager)
            self._bg_task_manager.shut_down()
            self._bg_task_manager = None

        self._bundle.current_dialog = None

        return QtGui.QWidget.closeEvent(self, event)

    def reload(self, timeout=None):
        """
        Reload the model with the monitor data.

        :param timeout: Refresh timetout
        """

        if timeout:
            time.sleep(timeout)

        if not os.path.exists(self._cache_folder):
            return

        for bg_cache_folder in os.listdir(self._cache_folder):

            monitor_file_path = os.path.join(self._cache_folder, bg_cache_folder, "monitor.yml")
            if not os.path.exists(monitor_file_path):
                continue

            if monitor_file_path not in self.__monitor_files:
                # add the monitor data to the model
                self._publish_tree_model.add_publish_tree(monitor_file_path)
                self.__monitor_files.append(monitor_file_path)
            else:
                # refresh the existing tree
                self._publish_tree_model.update_publish_tree(monitor_file_path)

    def _on_background_task_completed(self, uid, group_id, result):
        """
        Slot triggered when the background manager has finished doing some task. The only task we're asking the manager
        to do is to find the latest published file associated to the current item.
        :param uid:      Unique id associated with the task
        :param group_id: The group the task is associated with
        :param result:   The data returned by the task
        """
        if uid not in self._pending_requests:
            return
        self._pending_requests.remove(uid)

        task_id = self._bg_task_manager.add_task(
            self.reload,
            task_kwargs={"timeout": 3}
        )
        self._pending_requests.append(task_id)

    def _on_background_task_failed(self, uid, group_id, msg, stack_trace):
        """
        Slot triggered when the background manager fails to do some task.
        :param uid:         Unique id associated with the task
        :param group_id:    The group the task is associated with
        :param msg:         Short error message
        :param stack_trace: Full error traceback
        """

        if uid in self._pending_requests:
            self._pending_requests.remove(uid)

        self._bundle.logger.error("Error happening when reloading the data: {}".format(stack_trace))
