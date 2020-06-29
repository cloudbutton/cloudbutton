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

import multiprocessing


RUNTIME_NAME_DEFAULT = 'localhost'
RUNTIME_TIMEOUT_DEFAULT = 600  # 10 minutes


def load_config(config_data):
    config_data['cloudbutton']['runtime'] = RUNTIME_NAME_DEFAULT
    config_data['cloudbutton']['runtime_memory'] = None
    if 'runtime_timeout' not in config_data['cloudbutton']:
        config_data['cloudbutton']['runtime_timeout'] = RUNTIME_TIMEOUT_DEFAULT

    if 'storage_backend' not in config_data['cloudbutton']:
        config_data['cloudbutton']['storage_backend'] = 'localhost'

    if 'localhost' not in config_data:
        config_data['localhost'] = {}

    if 'ibm_cos' in config_data and 'private_endpoint' in config_data['ibm_cos']:
        del config_data['ibm_cos']['private_endpoint']

    if 'workers' in config_data['cloudbutton']:
        config_data['localhost']['workers'] = config_data['cloudbutton']['workers']
    else:
        total_cores = multiprocessing.cpu_count()
        config_data['cloudbutton']['workers'] = total_cores
        config_data['localhost']['workers'] = total_cores
