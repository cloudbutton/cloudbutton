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

import logging
import os
from cloudbutton.config import cloud_logging_config
from cloudbutton.engine.agent.handler import function_handler

cloud_logging_config(logging.INFO)
logger = logging.getLogger('__main__')


def main(event, context):
    logger.info("Starting AWS Lambda Function execution")
    os.environ['__OW_ACTIVATION_ID'] = context.aws_request_id
    os.environ['__PW_ACTIVATION_ID'] = context.aws_request_id
    function_handler(event)
    return {"Execution": "Finished"}

