import os
import logging
from cloudbutton.version import __version__
from cloudbutton.config import cloud_logging_config
from cloudbutton.engine.agent import function_handler
from cloudbutton.engine.agent import function_invoker

cloud_logging_config(logging.INFO)
logger = logging.getLogger('__main__')


def main(args):
    os.environ['__PW_ACTIVATION_ID'] = os.environ['__OW_ACTIVATION_ID']
    if 'remote_invoker' in args:
        logger.info("PyWren v{} - Starting OpenWhisk Functions invoker".format(__version__))
        function_invoker(args)
    else:
        logger.info("PyWren v{} - Starting OpenWhisk Functions execution".format(__version__))
        function_handler(args)

    return {"Execution": "Finished"}
