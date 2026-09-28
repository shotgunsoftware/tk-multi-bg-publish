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

        if current_engine.name == "tk-alias":
            if self._alias_uses_bundled_python(current_engine):
                alias_exec = current_engine.alias_execpath or os.environ.get("TK_ALIAS_EXECPATH")
                if not alias_exec:
                    raise Exception(
                        "Background publish for Alias requires TK_ALIAS_EXECPATH"
                    )
                python_exe = os.path.join(
                    os.path.dirname(alias_exec), "Python", "python.exe"
                )
                if not os.path.isfile(python_exe):
                    raise Exception(
                        "Alias 2027.1+ background publish requires bundled Python at "
                        f"{python_exe}"
                    )
                return python_exe
            return os.path.join(sys.prefix, "python.exe")

        if current_engine.name == "tk-vred":
            return sys.executable

        return None

    def get_subprocess_environment(self):
        """
        Build the environment to use when launching the publish script in a subprocess.

        :return: A dictionary where the key is the environment variable name and the value is the environment variable
            value. If None is returned, the subprocess will inherit of the current environment.
        """

        current_engine = self.parent.engine

        if current_engine.name == "tk-alias":

            env = os.environ.copy()
            env["TK_ALIAS_HAS_UI"] = "0"
            env["TK_ALIAS_OPEN_MODEL"] = "1"

            uses_bundled = self._alias_uses_bundled_python(current_engine)
            self._add_alias_license_to_env(env, current_engine, uses_bundled)

            if uses_bundled:
                env["PYTHONPATH"] = self._pythonpath_without_desktop_stdlib(
                    env.get("PYTHONPATH", "")
                )
                env.pop("PYTHONHOME", None)
                return env

            alias_exec = current_engine.alias_execpath or os.environ.get("TK_ALIAS_EXECPATH")
            if not alias_exec:
                raise Exception(
                    "Background publish for Alias requires TK_ALIAS_EXECPATH"
                )
            alias_bin = os.path.dirname(alias_exec)
            desktop_bin = os.path.dirname(sys.executable)
            if not env.get("PATH", "").startswith(desktop_bin):
                env["PATH"] = "{};{}".format(desktop_bin, env.get("PATH", ""))

            env["BG_PUBLISH_ALIAS_DLL_PATH"] = alias_bin

            alias_fw_path = os.environ.get("TK_FRAMEWORK_ALIAS_PYTHON_PATH")
            if not alias_fw_path:
                raise Exception(
                    "Background publish for Alias requires "
                    "TK_FRAMEWORK_ALIAS_PYTHON_PATH"
                )
            alias_version = os.environ.get("TK_ALIAS_VERSION") or current_engine.alias_version
            if not alias_version:
                raise Exception(
                    "Background publish for Alias requires TK_ALIAS_VERSION"
                )
            py_ver = "python{}.{}".format(
                sys.version_info.major, sys.version_info.minor
            )
            env["BG_PUBLISH_ALIAS_API_PATH"] = os.path.join(
                alias_fw_path,
                os.path.pardir,
                "dist",
                "Alias",
                py_ver,
                str(alias_version).strip().split()[0],
            )
            return env

        if current_engine.name == "tk-vred":
            env = os.environ.copy()
            env["SHOTGUN_ENABLE"] = "0"
            return env

        return None

    def _alias_uses_bundled_python(self, engine):
        """
        Return whether background publish should use Alias bundled Python.

        For Alias versions at or above ``ALIAS_BUNDLED_PYTHON_MIN_VERSION`` on
        the engine, the subprocess runs ``{Alias bin}/Python/python.exe`` instead
        of ShotGrid Desktop's interpreter.

        :param engine: The current Toolkit engine (``tk-alias``).
        :rtype: bool
        """
        version = os.environ.get("TK_ALIAS_VERSION") or engine.alias_version
        if not version:
            return False
        return (
            engine.compare_alias_versions(
                version, engine.ALIAS_BUNDLED_PYTHON_MIN_VERSION
            )
            >= 0
        )

    def _add_alias_license_to_env(self, env, engine, uses_bundled_python=False):
        """
        Copy Alias license fields into env vars for ``run_publish_process.py``.

        OpenModel on 2027.1+ only needs product key and version in the subprocess;
        older flows also pass license type and path (see ``BG_PUBLISH_ALIAS_API_PATH``).

        :param env: Subprocess environment dict to update.
        :param engine: The current Toolkit engine (``tk-alias``).
        :param uses_bundled_python: If True, only key and version are required.
        :raises Exception: If required license fields are missing.
        """
        lic = engine.alias_py.get_product_information()
        env["BG_PUBLISH_ALIAS_PRODUCT_KEY"] = lic.get("product_key")
        env["BG_PUBLISH_ALIAS_PRODUCT_VERSION"] = lic.get("product_version")
        env["BG_PUBLISH_ALIAS_PRODUCT_LIC_TYPE"] = lic.get("product_license_type")
        env["BG_PUBLISH_ALIAS_PRODUCT_LIC_PATH"] = lic.get("product_license_path")
        required = [
            env["BG_PUBLISH_ALIAS_PRODUCT_KEY"],
            env["BG_PUBLISH_ALIAS_PRODUCT_VERSION"],
        ]
        if not uses_bundled_python:
            required.extend(
                [
                    env["BG_PUBLISH_ALIAS_PRODUCT_LIC_TYPE"],
                    env["BG_PUBLISH_ALIAS_PRODUCT_LIC_PATH"],
                ]
            )
        if not all(required):
            raise Exception(
                "Missing Alias license information for background publish: {0}".format(
                    lic
                )
            )

    def _pythonpath_without_desktop_stdlib(self, pythonpath):
        """
        Remove ShotGrid Desktop Python install entries from ``PYTHONPATH``.

        Bundled Alias Python must not pick up Desktop's stdlib or site-packages
        (broken extensions such as ``_csv`` / ``hashlib``). Parent process paths
        are copied into the subprocess env first; this filters that list.

        :param pythonpath: ``PYTHONPATH`` value (``os.pathsep``-separated).
        :returns: Filtered ``PYTHONPATH`` string.
        """
        desktop_root = os.path.normcase(
            os.path.join(
                os.environ.get("ProgramFiles", r"C:\Program Files"),
                "Shotgun",
                "Python3",
            )
        )
        kept = []
        for entry in pythonpath.split(os.pathsep):
            entry = entry.strip()
            if not entry:
                continue
            norm = os.path.normcase(os.path.normpath(entry))
            if norm == desktop_root or norm.startswith(desktop_root + os.sep):
                continue
            kept.append(entry)
        return os.pathsep.join(kept)
