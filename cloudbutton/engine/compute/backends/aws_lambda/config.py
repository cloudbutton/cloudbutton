#
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

import sys
import tempfile
import os
from cloudbutton.engine.utils import version_str

RUNTIME_TIMEOUT_DEFAULT = 900  # Default timeout: 900 s == 15 min
RUNTIME_MEMORY_DEFAULT = 256  # Default memory: 256 MB
RUNTIME_MEMORY_MAX = 3008  # Max. memory: 3008 MB

MAX_CONCURRENT_WORKERS = 1000

LAYER_DIR_PATH = os.path.join(tempfile.gettempdir(), 'modules', 'python')
LAYER_ZIP_PATH = os.path.join(tempfile.gettempdir(), 'cloudbutton_dependencies.zip')
ACTION_ZIP_PATH = os.path.join(tempfile.gettempdir(), 'cloudbutton_aws_lambda.zip')

def load_config(config_data=None):
    if 'runtime_memory' not in config_data['cloudbutton']:
        config_data['cloudbutton']['runtime_memory'] = RUNTIME_MEMORY_DEFAULT
    if config_data['cloudbutton']['runtime_memory'] % 64 != 0:   # Adjust 64 MB memory increments restriction
        mem = config_data['cloudbutton']['runtime_memory']
        config_data['cloudbutton']['runtime_memory'] = (mem + (64 - (mem % 64)))
    if config_data['cloudbutton']['runtime_memory'] > RUNTIME_MEMORY_MAX:
        config_data['cloudbutton']['runtime_memory'] = RUNTIME_MEMORY_MAX
    if 'runtime_timeout' not in config_data['cloudbutton'] or \
        config_data['cloudbutton']['runtime_timeout'] > RUNTIME_TIMEOUT_DEFAULT:
        config_data['cloudbutton']['runtime_timeout'] = RUNTIME_TIMEOUT_DEFAULT
    if 'runtime' not in config_data['cloudbutton']:
        config_data['cloudbutton']['runtime'] = 'python'+version_str(sys.version_info)
    if 'workers' not in config_data['cloudbutton']:
        config_data['cloudbutton']['workers'] = MAX_CONCURRENT_WORKERS

    if 'aws' not in config_data and 'aws_lambda' not in config_data:
        raise Exception("'aws' and 'aws_lambda' sections are mandatory in the configuration")
    
    # Put credential keys to 'aws_lambda' dict entry
    config_data['aws_lambda'] = {**config_data['aws_lambda'], **config_data['aws']}

    required_parameters_0 = ('access_key_id', 'secret_access_key')
    if not set(required_parameters_0) <= set(config_data['aws']):
        raise Exception("'access_key_id' and 'secret_access_key' are mandatory under 'aws' section")

    if 'execution_role' not in config_data['aws_lambda']:
        raise Exception("'execution_role' is mandatory under 'aws_lambda' section")
    
    if 'compute_backend_region' not in config_data['cloudbutton'] \
        and 'region_name' not in config_data['aws_lambda']:
        raise Exception("'compute_backend_region' or 'region_name' not specified")
    else:
        config_data['aws_lambda']['region'] = config_data['aws_lambda']['region_name']
