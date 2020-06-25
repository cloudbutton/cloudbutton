#
# Copyright 2018 PyWren Team
# Copyright IBM Corp. 2020
# Copyright Cloudlab URV 2020
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import os
import json
import tempfile
import importlib
import logging.config
from cloudbutton.version import __version__

logger = logging.getLogger(__name__)

COMPUTE_BACKEND_DEFAULT = 'ibm_cf'
STORAGE_BACKEND_DEFAULT = 'ibm_cos'

STORAGE_BASE_FOLDER = "cloudbutton-data"
DOCKER_BASE_FOLDER = "cloudbutton-docker"
TEMP = os.path.realpath(tempfile.gettempdir())
STORAGE_FOLDER = os.path.join(TEMP, STORAGE_BASE_FOLDER)
DOCKER_FOLDER = os.path.join(TEMP, DOCKER_BASE_FOLDER)

JOBS_PREFIX = "cloudbutton.jobs"
TEMP_PREFIX = "cloudbutton.jobs/tmp"
LOGS_PREFIX = "cloudbutton.logs"
RUNTIMES_PREFIX = "cloudbutton.runtimes"


MAX_AGG_DATA_SIZE = 4  # 4MiB

HOME_DIR = os.path.expanduser('~')
CONFIG_DIR = os.path.join(HOME_DIR, '.cloudbutton')
CONFIG_FILE = os.path.join(CONFIG_DIR, 'config')
CACHE_DIR = os.path.join(CONFIG_DIR, 'cache')


def load_yaml_config(config_filename):
    import yaml
    with open(config_filename, 'r') as config_file:
        data = yaml.safe_load(config_file)

    return data


def dump_yaml_config(config_filename, data):
    import yaml
    if not os.path.exists(os.path.dirname(config_filename)):
        os.makedirs(os.path.dirname(config_filename))

    with open(config_filename, "w") as config_file:
        yaml.dump(data, config_file, default_flow_style=False)


def get_default_home_filename():
    default_home_filename = CONFIG_FILE
    if not os.path.exists(default_home_filename):
        default_home_filename = os.path.join(HOME_DIR, '.cloudbutton_config')

    return default_home_filename


def get_default_config_filename():
    """
    First checks .cloudbutton_config
    then checks CLOUDBUTTON_CONFIG_FILE environment variable
    then ~/.cloudbutton_config
    """
    if 'CLOUDBUTTON_CONFIG_FILE' in os.environ:
        config_filename = os.environ['CLOUDBUTTON_CONFIG_FILE']

    elif os.path.exists(".cloudbutton_config"):
        config_filename = os.path.abspath('.cloudbutton_config')

    else:
        config_filename = get_default_home_filename()

    logger.info('Getting configuration from {}'.format(config_filename))

    return config_filename


def default_config(config_data=None, config_overwrite={}):
    """
    First checks .cloudbutton_config
    then checks CLOUDBUTTON_CONFIG_FILE environment variable
    then ~/.cloudbutton_config
    """
    logger.info('Cloudbutton toolkit v{}'.format(__version__))
    logger.debug("Loading configuration")

    if not config_data:
        if 'CLOUDBUTTON_CONFIG' in os.environ:
            config_data = json.loads(os.environ.get('CLOUDBUTTON_CONFIG'))
        else:
            config_filename = get_default_config_filename()
            if config_filename is None:
                raise ValueError("could not find configuration file")
            config_data = load_yaml_config(config_filename)

    if 'cloudbutton' not in config_data:
        raise Exception("cloudbutton section is mandatory in configuration")

    # overwrite values provided by the user
    config_data['cloudbutton'].update(config_overwrite)

    if 'storage_bucket' not in config_data['cloudbutton']:
        raise Exception("storage_bucket is mandatory in cloudbutton section of the configuration")

    if 'compute_backend' not in config_data['cloudbutton']:
        config_data['cloudbutton']['compute_backend'] = COMPUTE_BACKEND_DEFAULT
    if 'storage_backend' not in config_data['cloudbutton']:
        config_data['cloudbutton']['storage_backend'] = STORAGE_BACKEND_DEFAULT

    if 'rabbitmq' in config_data:
        if config_data['rabbitmq'] is None \
           or 'amqp_url' not in config_data['rabbitmq'] \
           or config_data['rabbitmq']['amqp_url'] is None:
            del config_data['rabbitmq']

    cb = config_data['cloudbutton']['compute_backend']
    logger.debug("Loading Compute backend module: {}".format(cb))
    cb_config = importlib.import_module('cloudbutton.engine.compute.backends.{}.config'.format(cb))
    cb_config.load_config(config_data)

    sb = config_data['cloudbutton']['storage_backend']
    logger.debug("Loading Storage backend module: {}".format(sb))
    sb_config = importlib.import_module('cloudbutton.engine.storage.backends.{}.config'.format(sb))
    sb_config.load_config(config_data)

    return config_data


def extract_storage_config(config):
    storage_config = dict()
    sb = config['cloudbutton']['storage_backend']
    storage_config['backend'] = sb
    storage_config['bucket'] = config['cloudbutton']['storage_bucket']

    storage_config[sb] = config[sb]
    storage_config[sb]['user_agent'] = 'cloudbutton/{}'.format(__version__)
    if 'storage_backend_region' in config['cloudbutton']:
        storage_config[sb]['region'] = config['cloudbutton']['storage_backend_region']

    return storage_config


def extract_compute_config(config):
    compute_config = dict()
    cb = config['cloudbutton']['compute_backend']
    compute_config['backend'] = cb

    compute_config[cb] = config[cb]
    compute_config[cb]['user_agent'] = 'cloudbutton/{}'.format(__version__)
    if 'compute_backend_region' in config['cloudbutton']:
        compute_config[cb]['region'] = config['cloudbutton']['compute_backend_region']

    return compute_config


def default_logging_config(log_level='INFO'):
    if log_level == 'DEBUG_BOTO3':
        log_level = 'DEBUG'
        logging.getLogger('ibm_boto3').setLevel(logging.DEBUG)
        logging.getLogger('ibm_botocore').setLevel(logging.DEBUG)

    logging.config.dictConfig({
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
            },
        },
        'handlers': {
            'default': {
                'level': log_level,
                'class': 'logging.StreamHandler',
                'formatter': 'standard'
            },
        },
        'loggers': {
            '': {
                'handlers': ['default'],
                'level': log_level,
                'propagate': True
            }
        }
    })


def cloud_logging_config(log_level='INFO'):
    if log_level == 'DEBUG_BOTO3':
        log_level = 'DEBUG'
        logging.getLogger('ibm_boto3').setLevel(logging.DEBUG)
        logging.getLogger('ibm_botocore').setLevel(logging.DEBUG)

    logging.config.dictConfig({
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': '[%(levelname)s] %(name)s: %(message)s'
            },
        },
        'handlers': {
            'default': {
                'level': log_level,
                'class': 'logging.StreamHandler',
                'formatter': 'standard',
                'stream': 'ext://sys.stdout'
            },
        },
        'loggers': {
            '': {
                'handlers': ['default'],
                'level': log_level,
                'propagate': True
            }
        }
    })
