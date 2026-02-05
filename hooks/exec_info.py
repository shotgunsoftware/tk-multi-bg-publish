# Copyright (c) 2022 Autodesk, Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.

import os
import re
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
            # Ensure tk-alias engine is running in OpenModel (headless/batch mode)
            env["TK_ALIAS_OPEN_MODEL"] = "1"

            # Set environment variables for the background publish process to import the Alias api module
            # NOTE: this is a workaround to MSVC runtime DLL conflicts between the Alias api and PySide
            alias_exec_path = os.environ.get("TK_ALIAS_EXECPATH")
            if not alias_exec_path:
                raise Exception(
                    "Background publish for Alias requires TK_ALIAS_EXECPATH environment variable to be set"
                )
            env["BG_PUBLISH_ALIAS_DLL_PATH"] = os.path.dirname(alias_exec_path)
            # Get the api path for the python version that will run the background publish process
            api_path = os.path.dirname(current_engine.alias_py.__file__)
            bg_publish_python_version = (
                f"python{sys.version_info.major}.{sys.version_info.minor}"
            )
            api_path = re.sub(r"python\d+\.\d+", bg_publish_python_version, api_path)
            env["BG_PUBLISH_ALIAS_API_PATH"] = api_path

            # Get the Alias license info and set the environment variables for
            # the background publish process. The background process will use
            # the Alias OpenModel API, which requires setting the license info,
            # starting in Alias 2027.0
            alias_lic_info = current_engine.alias_py.get_product_information()
            product_key = alias_lic_info.get("product_key")
            product_version = alias_lic_info.get("product_version")
            product_license_type = alias_lic_info.get("product_license_type")
            product_license_path = alias_lic_info.get("product_license_path")

            if not all(
                [
                    product_key,
                    product_version,
                    product_license_type,
                    product_license_path,
                ]
            ):
                raise Exception(
                    f"""Missing Alias license informatin required for background publish:
                    product_key: {product_key}
                    product_version: {product_version}
                    product_license_type: {product_license_type}
                    product_license_path: {product_license_path}
                    """
                )
            env["BG_PUBLISH_ALIAS_PRODUCT_KEY"] = product_key
            env["BG_PUBLISH_ALIAS_PRODUCT_VERSION"] = product_version
            env["BG_PUBLISH_ALIAS_PRODUCT_LIC_TYPE"] = product_license_type
            env["BG_PUBLISH_ALIAS_PRODUCT_LIC_PATH"] = product_license_path

            return env

        # in case of VRED, we don't want to enable the automatic Flow Production Tracking integration in order to
        # control the engine start when bootstrapping
        elif current_engine.name == "tk-vred":
            env = os.environ.copy()
            env["SHOTGUN_ENABLE"] = "0"
            return env

        return None
