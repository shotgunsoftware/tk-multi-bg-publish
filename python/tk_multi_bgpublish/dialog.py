# Copyright (c) 2022 Autodesk, Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.

import os
import platform
import shutil
import subprocess
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
        self.__reload_timeout = self._bundle.get_setting("reload_timeout")

        # now load in the UI that was created in the UI designer
        self._ui = Ui_Dialog()
        self._ui.setupUi(self)

        # initialize a BackgroundTaskManager to be able to perform the reload action without locking anything
        self._pending_requests = []
        self._bg_task_manager = BackgroundTaskManager(self, max_threads=2)
        self._bg_task_manager.start_processing()
        shotgun_globals.register_bg_task_manager(self._bg_task_manager)

        # create the model to store all the publish sessions
        self._publish_tree_model = PublishTreeModel(self)
        self._ui.view.setModel(self._publish_tree_model)

        # create the delegate used to correctly display the model data into the view
        self._publish_tree_delegate = create_publish_tree_delegate(self._ui.view)
        self._ui.view.setItemDelegate(self._publish_tree_delegate)

        # register some signals/slots
        self._bg_task_manager.task_completed.connect(self._on_background_task_completed)
        self._bg_task_manager.task_failed.connect(self._on_background_task_failed)

        # initialize a context menu to add extra actions without polluting the UI
        self._ui.view.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self._ui.view.customContextMenuRequested.connect(self._on_context_menu_requested)

        # finally, load the data
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

        # close down background tasks
        if self._bg_task_manager:
            shotgun_globals.unregister_bg_task_manager(self._bg_task_manager)
            self._bg_task_manager.shut_down()
            self._bg_task_manager = None

        return QtGui.QWidget.closeEvent(self, event)

    def reload(self, timeout=None):
        """
        Reload the model with the monitor data.

        :param timeout: Refresh timeout
        """

        self._bundle.logger.debug("Start refreshing the model data...")

        if timeout:
            time.sleep(timeout)

        if not os.path.exists(self._cache_folder):
            return

        # parse the cache folder to get all the monitor files and fill the model
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

        # finally, delete the items which don't exist anymore
        files_to_remove = []
        for monitor_file_path in self.__monitor_files:
            if not os.path.exists(monitor_file_path):
                self._publish_tree_model.remove_publish_tree(monitor_file_path)
                files_to_remove.append(monitor_file_path)
        for f in files_to_remove:
            self.__monitor_files.remove(f)

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
            task_kwargs={"timeout": self.__reload_timeout}
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

    def _on_context_menu_requested(self, pnt):
        """
        Populate the context menu

        :param pnt: The position for the context menu relative to the source widget.
        """

        # get the selected model item
        selection_model = self._ui.view.selectionModel()
        if not selection_model:
            return

        indexes = selection_model.selectedIndexes()
        if len(indexes) != 1:
            return
        item = indexes[0].model().itemFromIndex(indexes[0])

        # build the context menu
        context_menu = QtGui.QMenu(self)

        # add the "Open Log Folder" menu action
        open_folder_action = QtGui.QAction("Open Log Folder", context_menu)
        open_folder_action.triggered[()].connect(lambda checked=False: self._open_log_folder(item))
        context_menu.addAction(open_folder_action)

        # add the "Delete all completed jobs" menu action
        delete_all_jobs_action = QtGui.QAction("Delete all completed jobs", context_menu)
        delete_all_jobs_action.triggered[()].connect(lambda checked=False: self._delete_all_jobs())
        context_menu.addAction(delete_all_jobs_action)

        # add the "Delete completed job" menu action
        # this one will only be added if all the session tasks have been completed
        if item.data(PublishTreeModel.ITEM_TYPE_ROLE) == PublishTreeModel.PUBLISH_SESSION:
            progress = item.data(PublishTreeModel.PROGRESS_ROLE)
        else:
            session_item = item.model().get_session_item(item.session_uuid)
            progress = session_item.data(PublishTreeModel.PROGRESS_ROLE)
        if progress == 100:
            delete_job_action = QtGui.QAction("Delete completed job", context_menu)
            delete_job_action.triggered[()].connect(lambda checked=False: self._delete_job(item))
            context_menu.addAction(delete_job_action)

        # map the point to a global position to display the context menu at the right location
        pnt = self.sender().mapToGlobal(pnt)
        context_menu.exec_(pnt)

    # ---------------------------------------------------------------------------------------------
    # Context menu actions
    # ---------------------------------------------------------------------------------------------

    def _open_log_folder(self, item):
        """
        Open the file explorer at the log folder location

        :param item: The selected model item
        """

        log_folder = item.data(PublishTreeModel.LOG_FOLDER_ROLE)
        if not os.path.exists(log_folder):
            self._bundle.logger.error("Couldn't open {}: doesn't exist on disk".format(log_folder))
            return

        cmd = None
        if platform.system() == "Windows":
            cmd = 'explorer "{}"'.format(log_folder)
        elif platform.system() == "Linux":
            cmd = 'xdg-open "{}"'.format(log_folder)
        elif platform.system() == "Darwin":
            cmd = 'open "{}"'.format(log_folder)

        if cmd is None:
            self._bundle.logger.error("Couldn't open {}: can't find a valid 'open' command".format(log_folder))
            return

        subprocess.Popen(cmd)

    def _delete_all_jobs(self):
        """
        Delete all the completed jobs
        """

        for r in range(self._publish_tree_model.rowCount()):
            item = self._publish_tree_model.item(r)
            progress = item.data(PublishTreeModel.PROGRESS_ROLE)
            if progress == 100:
                self._delete_job(item, reload=False)
        self.reload()

    def _delete_job(self, item, reload=True):
        """
        Delete a specific job

        :param item: The selected model item
        :param reload: If True, the model will be reloaded once the log folder has been deleted
        """

        log_folder = item.data(PublishTreeModel.LOG_FOLDER_ROLE)
        if not os.path.exists(log_folder):
            self._bundle.logger.error("Couldn't delete job: doesn't exist on disk anymore")
            return

        shutil.rmtree(log_folder)

        # finally, reload the model/view
        if reload:
            self.reload()
