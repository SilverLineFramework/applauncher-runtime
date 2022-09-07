#!/usr/bin/env python3
"""
Main entrypoint; Starts the runtime
"""

import argparse
import uuid
import logzero
from logzero import logger
import importlib

import release
from common.config import settings
from dynaconf import ValidationError

from mqtt.listner import MQTTListner
from runtime.runtime_mngr import RuntimeMngr

def main(args):
    """ Main entry point of the app """
    # Set a minimum log level
    logzero.loglevel(logzero.INFO)

    #logger.info(settings.runtime)

    # create launcher instance from settings option
    (launcher_module, launcher_class) = settings.get('launcher.class').rsplit('.', 1)
    logger.debug("[RuntimeMngr] Importing {}.{}".format(launcher_module, launcher_class))
    LauncherClass = getattr(importlib.import_module(launcher_module), launcher_class)
    launcher = LauncherClass()
    rtmngr = RuntimeMngr(launcher)

    # create runtime mngr instance
    rtmngr = RuntimeMngr()

    # pass runtime mngr as pubsub handler to mqtt client
    mqttc = MQTTListner(rtmngr, **settings.get('mqtt'))

    input("Press Enter to continue...\n")

if __name__ == "__main__":
    """ This is executed when run from the command line """
    parser = argparse.ArgumentParser()

    # Required positional argument
    #parser.add_argument("arg", help="Required positional argument")

    # Optional argument flag which defaults to False
    #parser.add_argument("-f", "--flag", action="store_true", default=False)

    # Optional argument which requires a parameter (eg. -d test)
    #parser.add_argument("-n", "--name", action="store", dest="name")

    # Optional verbosity counter (eg. -v, -vv, -vvv, etc.)
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Verbosity (-v, -vv, etc)")

    # Specify output of "--version"
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s (version {version})".format(version=release.__version__))

    args = parser.parse_args()
    try:
        main(args)
    except ValidationError as e:
         print("Settings validation error:", str(e))
