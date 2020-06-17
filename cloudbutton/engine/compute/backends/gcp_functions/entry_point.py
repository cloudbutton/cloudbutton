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

import logging
import json
import base64
from cloudbutton.engine.agent.handler import function_handler
from cloudbutton.config import cloud_logging_config

cloud_logging_config(logging.INFO)
logger = logging.getLogger('__main__')

def main(event, context):
    logger.info("Starting GCP Functions function execution")
    args = json.loads(base64.b64decode(event['data']).decode('utf-8'))
    function_handler(args)
    return 'OK'
