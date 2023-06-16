# Copyright (c) 2022 Autodesk, Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.

import os
import subprocess

from sgtk.platform import Application


class BackgroundPublisher(Application):
    """
    This is the :class:`sgtk.platform.Application` subclass that defines the
    top-level Background Publish Monitor interface.
    """

    def init_app(self):
        """
        Called as the application is being initialized
        """

        tk_multi_bgpublish = self.import_module("tk_multi_bgpublish")
        self._constants = tk_multi_bgpublish.constants

        if not self.engine.has_ui:
            return

        self._unique_panel_id = self.engine.register_panel(self.create_panel)

        self.engine.register_command(
            "Background Publish Monitor",
            self.create_panel,
            {"short_name": "bg_publish_monitor"},
        )

    @property
    def constants(self):
        return self._constants

    def create_dialog(self):
        """
        Shows the panel as a dialog.

        :returns: The widget associated with the dialog.
        """

        # try to find existing window in order to avoid having many instances of the same app opened at the same time
        app_dialog = None
        for qt_dialog in self.engine.created_qt_dialogs:
            if not hasattr(qt_dialog, "_widget"):
                continue
            app_name = qt_dialog._widget.property("app_name")
            if app_name == self.name:
                app_dialog = qt_dialog
                break

        if app_dialog:
            app_dialog.raise_()
            app_dialog.activateWindow()
        else:
            tk_multi_bgpublish = self.import_module("tk_multi_bgpublish")
            app_dialog = self.engine.show_dialog(
                self.display_name,
                self,
                tk_multi_bgpublish.AppDialog,
            )
            app_dialog.setProperty("app_name", self.name)

        return app_dialog

    def create_panel(self):
        """
        Shows the UI as a panel.
        Note that since panels are singletons by nature,
        calling this more than once will only result in one panel.

        :returns: The widget associated with the panel.
        """

        tk_multi_bgpublish = self.import_module("tk_multi_bgpublish")

        # start the UI
        try:
            widget = self.engine.show_panel(
                self._unique_panel_id,
                self.display_name,
                self,
                tk_multi_bgpublish.AppDialog,
            )
        except AttributeError as e:
            # just to gracefully handle older engines and older cores
            self.logger.warning(
                "Could not execute show_panel method - please upgrade "
                "to latest core and engine! Falling back on show_dialog. "
                "Error: %s" % e
            )
            widget = self.create_dialog()

        return widget

    def launch_publish_process(self, publish_tree_file_path):
        """
        Launch the background publishing process

        :param publish_tree_file_path: Path to the publish tree file where all the publish information are stored
        """

        publish_app = self.engine.apps.get("tk-multi-publish2")
        if not publish_app:
            self.logger.error("Couldn't find Publisher app")
            return

        if not os.path.exists(publish_tree_file_path):
            self.logger.error(
                "Couldn't find {} publish tree file on disk".format(
                    publish_tree_file_path
                )
            )
            return

        monitor_file_path = os.path.join(
            os.path.dirname(publish_tree_file_path), "monitor.yml"
        )
        if not os.path.exists(monitor_file_path):
            self.logger.error(
                "Couldn't find {} monitor publish file on disk".format(
                    monitor_file_path
                )
            )
            return

        # find the right executable to use to execute the publish process
        executable_path = self.execute_hook_method(
            "exec_info_hook", "get_executable_path"
        )
        if not os.path.exists(executable_path):
            self.logger.error(
                "Couldn't find a valid path on disk for {}".format(executable_path)
            )
            return

        # get the path to the script we want to run
        script_path = os.path.join(
            self.disk_location, "scripts", "run_publish_process.py"
        )
        if not os.path.exists(script_path):
            self.logger.error(
                "Couldn't find a valid path on disk for {}".format(script_path)
            )
            return

        entity_dict = None
        if self.context.task:
            entity_dict = self.context.task
        elif self.context.entity:
            entity_dict = self.context.entity
        elif self.context.project:
            entity_dict = self.context.project

        # in case of VRED, the command line is slightly different
        if self.engine.name == "tk-vred":

            # we're using a dummy argument as first argument in order to have the same argument order when parsing them
            # in the script to run
            python_cmd = ""
            python_cmd += "import sys;"
            python_cmd += "sys.path.append(r'{}');".format(os.path.dirname(script_path))
            python_cmd += "import run_publish_process;"
            python_cmd += (
                "run_publish_process.main('{engine_name}', {pc_id}, {entity_dict}, r'{publish_tree_path}', "
                "r'{monitor_file_path}');".format(
                    engine_name=self.engine.name,
                    pc_id=self.sgtk.pipeline_configuration.get_shotgun_id(),
                    entity_dict=entity_dict,
                    publish_tree_path=publish_tree_file_path,
                    monitor_file_path=monitor_file_path,
                )
            )

            # VRED 2024 introduces Python Sandbox which requires authorization to run python
            # scripts; however, the prompt to authorize is not shown when running with
            # -hide_gui. So, we will need to add the '-insecure_python' flag to allow running
            # our script. The alternative not using this flag, would be that the user must
            # turn of Python Sandbox from Preferences>Scripts, or specify our module as allowed
            cmd = [executable_path, "-hide_gui", "-insecure_python", "-postpython", python_cmd]

        else:
            cmd = [
                executable_path,
                script_path,
                self.engine.name,
                str(self.sgtk.pipeline_configuration.get_shotgun_id()),
                str(entity_dict),
                publish_tree_file_path,
                monitor_file_path,
            ]

        # modify the STARTUPINFO to run the subprocess in silent mode
        startup_info = subprocess.STARTUPINFO()
        startup_info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startup_info.wShowWindow |= subprocess.SW_HIDE

        env = self.execute_hook_method("exec_info_hook", "get_subprocess_environment")

        subprocess.Popen(cmd, startupinfo=startup_info, env=env)
