# Copyright (c) 2022 Autodesk, Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.

import os
import sys

import sgtk

HookBaseClass = sgtk.get_hook_baseclass()


class AppUtilities(HookBaseClass):
    def get_executable_path(self):
        """
        Get the path to the executable to use to run the publish script.

        :return: The path to the executable
        """

        current_engine = self.parent.engine

        if current_engine.name == "tk-maya":
            maya_folder = os.path.dirname(sys.executable)
            return os.path.join(maya_folder, "mayapy.exe")

        elif current_engine.name == "tk-alias":
            return os.path.join(sys.prefix, "python.exe")

        elif current_engine.name == "tk-vred":
            return sys.executable

        return None

    def get_subprocess_environment(self):
        """
        Build the environment to use when launching the publish script in a subprocess.

        :return: A dictionary where the key is the environment variable name and the value is the environment variable
            value. If None is returned, the subprocess will inherit of the current environment.
        """

        current_engine = self.parent.engine

        # in case of Alias, we need to make sure the path to the Alias executable is first in the PATH environment
        # variable
        if current_engine.name == "tk-alias":
            env = os.environ.copy()
            alias_bin_folder = os.path.dirname(sys.executable)
            if not env.get("PATH", "").startswith(alias_bin_folder):
                env["PATH"] = "{};{}".format(alias_bin_folder, env.get("PATH", ""))
            return env

        # in case of VRED, we don't want to enable the automatic ShotGrid integration in order to control the engine
        # start when bootstrapping
        elif current_engine.name == "tk-vred":
            env = os.environ.copy()
            env["SHOTGUN_ENABLE"] = "0"
            return env

        return None
