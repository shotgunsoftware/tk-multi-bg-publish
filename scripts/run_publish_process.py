# Copyright (c) 2022 Autodesk, Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.

import ast
import logging
import os
import sys

import sgtk
from tank_vendor import yaml


def change_progress_status(
    monitor_file_path,
    item_uuid,
    process_status,
    task_uuid=None,
    previous_task_uuid=None,
    finish_status=None,
):
    """
    Update the monitor file once a task/item has been processed.

    :param monitor_file_path: Path to the monitor file
    :param item_uuid: UUID of the item to update
    :param process_status: Value of the status to update the task to
    :param task_uuid: UUID of the task to update
    :param previous_task_uuid: UUID of the task that has been processed just before the given one
    :param finish_status: Value of the status to update the previous task with
    """

    # open the monitor file to get the monitor data
    with open(monitor_file_path, "r") as fp:
        monitor_data = yaml.load(fp, Loader=yaml.FullLoader)

    for item in monitor_data["items"]:
        # change the status of the item if it has not been done yet
        if item["uuid"] == item_uuid and item["status"] != process_status:
            item["status"] = process_status
        # if a task UUID is provided, try to find the corresponding task to change its status
        if task_uuid:
            for task in item["tasks"]:
                # find that task, update its status
                if task["uuid"] == task_uuid:
                    task["status"] = process_status
                # if a UUID has been provided for the previous task, find the task and update its status
                elif (
                    previous_task_uuid
                    and task["uuid"] == previous_task_uuid
                    and finish_status
                ):
                    task["status"] = finish_status
                else:
                    continue

    # finally, save the data into the monitor file
    with open(monitor_file_path, "w") as fp:
        yaml.safe_dump(monitor_data, fp)


def change_failed_task_status(monitor_file_path, progress_status, failed_status):
    """
    One a task has failed during one of the publishing step, try to find which one and update its status.

    :param monitor_file_path: Path to the monitor file
    :param progress_status: Value of the progress status
    :param failed_status: Value of the failed status
    """

    # open the monitor file to get the data
    with open(monitor_file_path, "r") as fp:
        monitor_data = yaml.load(fp, Loader=yaml.FullLoader)

    # go through each item/tasks to find which one is the first with the progress status: it will be the failing task
    for item in monitor_data["items"]:
        for task in item["tasks"]:
            if task["status"] != progress_status:
                continue
            task["status"] = failed_status
            item["status"] = failed_status
            break

    # finally, save the data into the monitor file
    with open(monitor_file_path, "w") as fp:
        yaml.safe_dump(monitor_data, fp)


def task_generator(tree, monitor_file_path, process_status, finished_status):
    """
    Custom iterator on the publish tasks. It will yield the next task and change its status as well as the status of
    the previous task.

    :param tree: Publish Tree to go through
    :param monitor_file_path: Path to the monitor file
    :param process_status: Value of the status to update the task to
    :param finished_status: Value of the status to update the previous task to
    """
    previous_task = None
    for item in tree:
        for task in item.tasks:
            if task.active:
                task_uuid = task.settings["Task UUID"].value
                previous_task_uuid = (
                    None
                    if not previous_task
                    else previous_task.settings["Task UUID"].value
                )
                # change the status of the task before returning it
                change_progress_status(
                    monitor_file_path,
                    item.properties.uuid,
                    process_status,
                    task_uuid=task_uuid,
                    previous_task_uuid=previous_task_uuid,
                    finish_status=finished_status,
                )
                previous_task = task
                yield task
        # once all the tasks have been done, change the status of the item itself
        if item.properties.get("uuid"):
            change_progress_status(
                monitor_file_path, item.properties.uuid, finished_status
            )


def main(
    engine_name,
    pipeline_config_id,
    entity_dict,
    publish_tree,
    monitor_file_path,
):
    """
    Main function of the script which launch the background publishing process.
    It will be responsible for:
     - initializing the environment
     - bootstrapping the engine
     - open the session work file
     - use the Publish API to create a manager and run the publish/finalize steps
    As soon as a step for a task is done, the task status will be updated in the monitor.yml file. This file will be
    used by the monitor UI to display the publish progress.

    :param engine_name: Name of the engine to launch
    :param pipeline_config_id: ID of the pipeline config to use when bootstrapping the engine
    :param entity_dict: ShotGrid dictionary of the entity to use when bootstrapping the engine
    :param publish_tree: Path to the file to use to load the publish tree
    :param monitor_file_path: Path to the file to use to monitor the publish process
    """

    # initialize a log handler
    log_path = os.path.join(os.path.dirname(monitor_file_path), "bg_publish.log")
    log_handler = logging.FileHandler(log_path)
    sgtk.LogManager().initialize_custom_handler(log_handler)

    # initialize the environment
    if engine_name == "tk-maya":
        import maya.standalone

        maya.standalone.initialize()
        import maya.cmds as cmds

        # import pymel to be sure everything has been sourced and imported
        import pymel.core as pm
    elif engine_name == "tk-alias":
        import alias_api

        alias_api.initialize_universe()
    elif engine_name == "tk-vred":
        import vrController
        import vrFileIO
        import vrScenegraph

    # bootstrap the engine
    mgr = sgtk.bootstrap.ToolkitManager()
    mgr.plugin_id = "basic.desktop"
    mgr.pipeline_configuration = pipeline_config_id
    mgr.bootstrap_engine(engine_name, entity_dict)

    current_engine = sgtk.platform.current_engine()
    publish_app = current_engine.apps.get("tk-multi-publish2")
    bg_publish_app = current_engine.apps.get("tk-multi-bg-publish")

    # load the publish tree
    # manager = publish_app.create_publish_manager(publish_logger=current_engine.logger)
    manager = publish_app.create_publish_manager(publish_logger=log_handler)
    manager.load(publish_tree)

    # modify the publish tree to indicate that we're now processing in background mode
    manager.tree.root_item.properties["in_bg_process"] = True
    manager.save(publish_tree)

    # get the latest item of the tree - we'll need it later to update the statuses
    # same for the task
    latest_item = None
    for item in manager.tree:
        if item.properties.get("uuid"):
            latest_item = item
    latest_task = None
    for task in latest_item.tasks:
        if task.active:
            latest_task = task

    # open the file we want to perform operations on
    session_path = manager.tree.root_item.properties.get("session_path")
    if engine_name == "tk-maya":
        cmds.file(session_path, open=True, force=True)
    elif engine_name == "tk-alias":
        alias_api.open_file(session_path)
    elif engine_name == "tk-vred":
        vrFileIO.load(
            [session_path],
            vrScenegraph.getRootNode(),
            newFile=True,
            showImportOptions=False,
        )

    # run publish() method for each task
    # we're using a custom task iterator in order to be able to update the task status once an action is done
    try:
        manager.publish(
            task_generator=task_generator(
                manager.tree,
                monitor_file_path,
                bg_publish_app.constants.PUBLISH_IN_PROGRESS,
                bg_publish_app.constants.PUBLISH_FINISHED,
            )
        )
        # change the status of the last task/item once everything is completed
        change_progress_status(
            monitor_file_path,
            latest_item.properties.uuid,
            bg_publish_app.constants.PUBLISH_FINISHED,
            task_uuid=latest_task.settings["Task UUID"].value,
        )

    # if an error occurred during the publish process, try to find which task has failed and update the status
    # accordingly
    except Exception as e:
        current_engine.logger.error(
            "Error happening during publish process: {} ".format(e)
        )
        change_failed_task_status(
            monitor_file_path,
            bg_publish_app.constants.PUBLISH_IN_PROGRESS,
            bg_publish_app.constants.PUBLISH_FAILED,
        )

    # if all the publish tasks have been done without failing, run finalize() method
    else:
        try:
            manager.finalize(
                task_generator=task_generator(
                    manager.tree,
                    monitor_file_path,
                    bg_publish_app.constants.FINALIZE_IN_PROGRESS,
                    bg_publish_app.constants.FINALIZE_FINISHED,
                )
            )
            change_progress_status(
                monitor_file_path,
                latest_item.properties.uuid,
                bg_publish_app.constants.FINALIZE_FINISHED,
                task_uuid=latest_task.settings["Task UUID"].value,
            )

        # if an error occurred during the publish process, try to find which task has failed and update the status
        # accordingly
        except Exception as e:
            current_engine.logger.error(
                "Error happening during finalize process: {} ".format(e)
            )
            change_failed_task_status(
                monitor_file_path,
                bg_publish_app.constants.FINALIZE_IN_PROGRESS,
                bg_publish_app.constants.FINALIZE_FAILED,
            )

    finally:
        if engine_name == "tk-vred":
            vrController.terminateVred()
        # shutdown the engine
        current_engine.destroy()


if __name__ == "__main__":

    main(
        sys.argv[1],
        int(sys.argv[2]),
        ast.literal_eval(sys.argv[3]),
        sys.argv[4],
        sys.argv[5],
    )
