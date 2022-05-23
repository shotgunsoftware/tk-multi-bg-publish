# Copyright (c) 2022 Autodesk, Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.

# the publish process statuses - we are storing them in another file in order to be able
# to access them from other applications
(
    WAITING_TO_START,
    PUBLISH_IN_PROGRESS,
    PUBLISH_FINISHED,
    PUBLISH_FAILED,
    FINALIZE_IN_PROGRESS,
    FINALIZE_FINISHED,
    FINALIZE_FAILED,
    WARNING,
) = range(8)
