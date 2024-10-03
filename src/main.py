#!/usr/bin/env python3
"""
Main entrypoint; Starts the runtime
"""

import argparse
import json
import logzero
from logzero import logger
import time

import release
from common.config import settings
from dynaconf import ValidationError

from pubsub.listner import MQTTListner
from runtime.runtime_mngr import RuntimeMngr

# print settings with no password
def print_settings():
    s_dict = settings.as_dict()
    s_dict['MQTT'].pop('password')
    logger.debug("Runtime settings: ")
    logger.debug(json.dumps(s_dict, indent=4))
    
def main(args):
    """ Main entry point of the app """    

    print_settings()

    # Set a minimum log level
    loglevel = getattr(logzero, settings.loglevel)
    logzero.loglevel(loglevel)

    # create runtime mngr instance
    rtmngr = RuntimeMngr()

    # pass runtime mngr as pubsub handler to mqtt client
    mqttc = MQTTListner(rtmngr, **settings.get('mqtt'), error_topic=settings.topics.runtimes)

    # some time to init (just so following message does not appear in the middle of init log)
    time.sleep(2)
    
    while True:
        choice = input("\nEnter Q to quit.\n")
        if choice.lower() == "q":
            break

if __name__ == "__main__":
    """ This is executed when run from the command line """
    parser = argparse.ArgumentParser()

    # Optional verbosity counter (eg. -v, -vv, -vvv, etc.)
    # parser.add_argument(
    #     "-v",
    #     "--verbose",
    #     action="count",
    #     default=0,
    #     help="Verbosity (-v, -vv, etc)")

    # Specify output of "--version"
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s (version {version})".format(version=release.__version__))

    parser.add_argument(
        "--daemon",
        action="store_true")

    args = parser.parse_args()
    
    try:
        main(args)
    except ValidationError as e:
         print("Settings validation error:", str(e))
    except Exception as e:
        print(str(e))
