import os
import shutil
import logging
import boto3
import botocore.session
import time
import json
import zipfile
import sys
import subprocess
import tempfile
import textwrap
import cloudbutton
from . import config as aws_lambda_config

logger = logging.getLogger(__name__)


class AWSLambdaBackend:
    """
    A wrap-up around AWS Boto3 Lambda API
    """

    def __init__(self, aws_lambda_config):
        self.log_level = os.getenv('CLOUDBUTTON_LOGLEVEL')
        self.name = 'aws_lambda'
        self.aws_lambda_config = aws_lambda_config
        self.package = 'cloudbutton_v'+cloudbutton.__version__
        self.region = aws_lambda_config['region']
        self.role = aws_lambda_config['execution_role']
        self.layer_key = self.package.replace('.', '-')+'_dependencies'

        self.session = boto3.Session(aws_access_key_id=aws_lambda_config['access_key_id'],
                                     aws_secret_access_key=aws_lambda_config['secret_access_key'],
                                     region_name=self.region)
        self.client = self.session.client('lambda', region_name=self.region)

        log_msg = 'Cloudbutton v{} init for AWS Lambda - Region: {}'.format(cloudbutton.__version__, self.region)
        logger.info(log_msg)
        if not self.log_level:
            print(log_msg)

    def _format_action_name(self, runtime_name, runtime_memory):
        runtime_name = (self.package+'_'+runtime_name).replace('.', '-')
        return '{}_{}MB'.format(runtime_name, runtime_memory)
    
    def _unformat_action_name(self, action_name):
        split = action_name.split('_')
        runtime_name = split[1].replace('-', '.')
        runtime_memory = int(split[2].replace('MB', ''))
        return runtime_name, runtime_memory
        
    def _check_dependencies_layer(self, runtime_name):
        """
        Checks if Cloudbutton dependencies layer is already deployed
        returns : arn if deployed, else None
        """
        layers = self.list_layers(runtime_name)
        dep_layer = list(filter(lambda x: x['LayerName'] == self.layer_key, layers))
        if len(dep_layer) != 0:
            layer = dep_layer.pop()
            arn = layer['LatestMatchingVersion']['LayerVersionArn']
        else:
            arn = None
        return arn
    
    def _get_scipy_layer_arn(self, runtime_name):
        """
        Retruns arn for the existing numerics lambda layer basen on region
        return : layer arn
        """
        # TODO complete list with all regions
        acc_id = {
            'us-east-1' : 668099181075,
            'us-east-2' : 259788987135,
            'us-west-1' : 325793726646,
            'us-west-2' : 420165488524,
            'eu-central-1' : 292169987271,
            'eu-west-1' : 399891621064,
            'eu-west-2' : 142628438157,
            'eu-west-3' : 959311844005,
            'eu-north-1' : 642425348156
        }
        
        runtime_name = runtime_name.replace('p', 'P').replace('.', '')
        arn = 'arn:aws:lambda:'+self.region+':'+str(acc_id[self.region])+':layer:AWSLambda-'+runtime_name+'-SciPy1x:2'
        return arn
    
    def _build_dependencies_layer(self):
        """
        Downloads and builds module dependencies for Cloudbutton lambda execution
        return : layer zip bytes
        """
        def add_folder_to_zip(zip_file, full_dir_path, sub_dir=''):
            for file in os.listdir(full_dir_path):
                full_path = os.path.join(full_dir_path, file)
                if os.path.isfile(full_path):
                    zip_file.write(full_path, os.path.join(sub_dir, file), zipfile.ZIP_DEFLATED)
                elif os.path.isdir(full_path) and '__pycache__' not in full_path:
                    add_folder_to_zip(zip_file, full_path, os.path.join(sub_dir, file))

        # Path where modules will be downloaded
        if os.path.exists(aws_lambda_config.LAYER_DIR_PATH) and os.path.isdir(aws_lambda_config.LAYER_DIR_PATH):
            shutil.rmtree(aws_lambda_config.LAYER_DIR_PATH)
        elif os.path.exists(aws_lambda_config.LAYER_DIR_PATH) and os.path.isfile(aws_lambda_config.LAYER_DIR_PATH):
            os.remove(aws_lambda_config.LAYER_DIR_PATH)
        if not (os.path.isdir(aws_lambda_config.LAYER_DIR_PATH)):
            os.makedirs(aws_lambda_config.LAYER_DIR_PATH)
        
        # Get modules name & version from requirements.txt
        base_path = os.path.dirname(os.path.abspath(cloudbutton.__file__))
        requirements_path = os.path.join(base_path, 'engine', 'backends', 'compute', 'aws_lambda', 'requirements.txt')
        dependencies = []

        with open(requirements_path, 'r') as requirements_file:
            dependencies = requirements_file.readlines()
        
        # Install modules
        dependencies = list(filter(lambda x : x.rstrip(), dependencies))
        dependencies = list(map(lambda x : x.replace('\n', ''), dependencies))
        # old_stdout = sys.stdout     # Disable stdout
        # sys.stdout = open(os.devnull, 'w')
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-t', aws_lambda_config.LAYER_DIR_PATH, '--system'] + dependencies)
        # sys.stdout = old_stdout

        # Compress modules
        with zipfile.ZipFile(aws_lambda_config.LAYER_ZIP_PATH, 'w') as layer_zip:
            add_folder_to_zip(layer_zip, os.path.join(tempfile.gettempdir(), 'modules'))

        # Read zip as bytes
        with open(aws_lambda_config.LAYER_ZIP_PATH, 'rb') as layer_zip:
            layer_bytes = layer_zip.read()
        
        return layer_bytes
    
    def _setup_layers(self, runtime_name):
        """
        Setups and creates lambda layers for Cloudbutton function execution
        """
        layers_arn = []
        dependencies_layer = self._check_dependencies_layer(runtime_name)

        if dependencies_layer is None:
            layer_bytes = self._build_dependencies_layer()
            # Upload dependencies layer from bytes zip
            dependencies_layer = self.create_layer(
                self.layer_key,
                runtime_name,
                layer_bytes)
        
        layers_arn.append(dependencies_layer)
        layers_arn.append(self._get_scipy_layer_arn(runtime_name))
        return layers_arn

    def _create_handler_bin(self):
        """
        Creates Cloudbutton handler zip
        return : zip binary
        """
        logger.debug("Creating function handler zip in {}".format(aws_lambda_config.ACTION_ZIP_PATH))

        def add_folder_to_zip(zip_file, full_dir_path, sub_dir=''):
            for file in os.listdir(full_dir_path):
                full_path = os.path.join(full_dir_path, file)
                if os.path.isfile(full_path):
                    zip_file.write(full_path, os.path.join('cloudbutton', sub_dir, file), zipfile.ZIP_DEFLATED)
                elif os.path.isdir(full_path) and '__pycache__' not in full_path:
                    add_folder_to_zip(zip_file, full_path, os.path.join(sub_dir, file))

        try:
            with zipfile.ZipFile(aws_lambda_config.ACTION_ZIP_PATH, 'w') as cloudbutton_zip:
                current_location = os.path.dirname(os.path.abspath(__file__))
                module_location = os.path.dirname(os.path.abspath(cloudbutton.__file__))
                main_file = os.path.join(current_location, 'entry_point.py')
                cloudbutton_zip.write(main_file, '__main__.py', zipfile.ZIP_DEFLATED)
                add_folder_to_zip(cloudbutton_zip, module_location)

            with open(aws_lambda_config.ACTION_ZIP_PATH, "rb") as action_zip:
                action_bin = action_zip.read()
        except Exception as e:
            raise Exception('Unable to create the {} package: {}'.format(aws_lambda_config.ACTION_ZIP_PATH, e))
        return action_bin
        
    
    def build_runtime(self):
        pass

    def update_runtime(self, runtime_name, code, memory=3008, timeout=900):
        """
        Updates code, memory and time of existing lambda function
        """
        function_name = self._format_action_name(runtime_name, memory)        
        logger.debug('Updating function {} code/config'.format(function_name))

        response = self.client.update_function_code(
            FunctionName=function_name,
            ZipFile=code,
            Publish=False
        )

        if response['ResponseMetadata']['HTTPStatusCode'] == 201:
            logger.debug("OK --> Updated function code {}".format(function_name))
        else:
            msg = 'An error occurred updating function code {}: {}'.format(function_name, response)
            raise Exception(msg)

        layers = self._setup_layers(runtime_name)

        response = self.client.update_function_configuration(
            FunctionName=function_name,
            Role=self.role,
            Timeout=timeout,
            MemorySize=memory,
            Layers=layers
        )

        if response['ResponseMetadata']['HTTPStatusCode'] == 201:
            logger.debug("OK --> Updated function config {}".format(function_name))
        else:
            msg = 'An error occurred updating function config {}: {}'.format(function_name, response)
            raise Exception(msg)

    def create_runtime(self, runtime_name, memory=3008, code=None, timeout=900):
        """
        Create an AWS Lambda function
        """
        function_name = self._format_action_name(runtime_name, memory)
        logger.debug('Creating new lambda runtime: {}'.format(function_name))

        layers = self._setup_layers(runtime_name)

        runtime_meta = self._generate_runtime_meta(runtime_name)

        if code is None:
            code = self._create_handler_bin()

        try:
            response = self.client.create_function(
                FunctionName=function_name,
                Runtime=runtime_name,
                Role=self.role,
                Handler='__main__.main',
                Code={
                    'ZipFile': code
                },
                Description=self.package,
                Timeout=timeout,
                MemorySize=memory,
                Layers=layers
            )

            if response['ResponseMetadata']['HTTPStatusCode'] == 201:
                logger.debug("OK --> Created action {}".format(runtime_name))
            else:
                msg = 'An error occurred creating/updating action {}: {}'.format(runtime_name, response)
                raise Exception(msg)        
        except self.client.exceptions.ResourceConflictException:
            logger.debug('{} lambda function already exists. It will be replaced.')
            self.update_runtime(runtime_name, code, memory, timeout)
        
        return runtime_meta

    def delete_runtime(self, runtime_name, memory):
        """
        Deletes lambda runtime from its runtime name and memory
        """
        logger.debug('Deleting lambda runtime: {}'.format(runtime_name))

        function_name = self._format_action_name(runtime_name, memory)
        
        response = self.client.delete_function(
            FunctionName=function_name
        )

        if response['ResponseMetadata']['HTTPStatusCode'] == 204:
            logger.debug("OK --> Deleted function {}".format(runtime_name))
        else:
            msg = 'An error occurred creating/updating action {}: {}'.format(runtime_name, response)
            raise Exception(msg)

    def delete_all_runtimes(self):
        """
        Deletes all Cloudbutton Lambda runtimes
        """
        logger.debug('Deleting all runtimes')
        
        response = self.client.list_functions(
            MasterRegion=self.region
        )

        for runtime in response['Functions']:
            if 'cloudbutton_v' in runtime['FunctionName']:
                runtime_name, runtime_memory = self._unformat_action_name(runtime['FunctionName'])
                self.delete_runtime(runtime_name, runtime_memory)

    def list_runtimes(self, docker_image_name='all'):
        """
        List all the lambda runtimes deployed.
        return: Array of tuples (function_name, memory)
        """
        runtimes = []
        response = self.client.list_functions(
            MasterRegion=self.region
        )

        for runtime in response['Functions']:
            function_name = runtime['FunctionName']
            memory = runtime['MemorySize']
            runtimes.append((function_name, memory))
        return runtimes

    def create_layer(self, layer_name, runtime_name, zipfile):
        """
        Creates lambda layer from bin code
        """
        logger.debug("Creating lambda layer: {}".format(layer_name))
        response = self.client.publish_layer_version(
            LayerName=layer_name,
            Description=self.package,
            Content={
                'ZipFile': zipfile
            },
            CompatibleRuntimes=[runtime_name]
        )

        if response['ResponseMetadata']['HTTPStatusCode'] == 201:
            logger.debug("OK --> Layer {} created".format(layer_name))
            return response['LayerVersionArn']
        else:
            msg = 'An error occurred creating layer {}: {}'.format(layer_name, response)
            raise Exception(msg)
    
    def delete_layer(self, layer_arn, version_number=None):
        """
        Deletes lambda layer from its arn
        """
        logger.debug("Deleting lambda layer: {}".format(layer_arn))

        if version_number is None:
            version_number = layer_arn.split(':')[-1]

        response = self.client.delete_layer_version(
            LayerName=layer_arn,
            VersionNumber=version_number
        )

        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            logger.debug("OK --> Layer {} deleted".format(layer_arn))
            return response['LayerVersionArn']
        else:
            msg = 'An error occurred deleting layer {}: {}'.format(layer_arn, response)
            raise Exception(msg)

    def list_layers(self, runtime_name=None):
        """
        Gets all Lambda Layers available for the Python runtime selected
        """
        logger.debug("Listing lambda layers: {}".format(runtime_name))
        response = self.client.list_layers(
            CompatibleRuntime=runtime_name
        )

        return response['Layers']

    def invoke(self, runtime_name, runtime_memory, payload, self_invoked=False):
        """
        Invoke lambda function asynchronously
        """
        exec_id = payload['executor_id']
        call_id = payload['call_id']

        function_name = self._format_action_name(runtime_name, runtime_memory)

        start = time.time()
        try:
            response = self.client.invoke(
                FunctionName=function_name,
                InvocationType='Event',
                Payload=json.dumps(payload)
            )
        except Exception as e:
            log_msg = ('ExecutorID {} - Function {} invocation failed: {}'.format(exec_id, call_id, str(e)))
            logger.debug(log_msg)
            if self_invoked:
                return None
            return self.invoke(runtime_name, runtime_memory, payload, self_invoked=True)

        roundtrip = time.time() - start
        resp_time = format(round(roundtrip, 3), '.3f')

        if response['ResponseMetadata']['HTTPStatusCode'] == 202:
            log_msg = ('ExecutorID {} - Function {} invocation done! ({}s) - Activation ID: '
                       '{}'.format(exec_id, call_id, resp_time, response['ResponseMetadata']['RequestId']))
            logger.debug(log_msg)
            return response['ResponseMetadata']['RequestId']
        else:
            logger.debug(response)
            if response['ResponseMetadata']['HTTPStatusCode'] == 401:
                raise Exception('Unauthorized - Invalid API Key')
            elif response['ResponseMetadata']['HTTPStatusCode'] == 404:
                raise Exception('Cloudbutton Runtime: {} not deployed'.format(runtime_name))
            elif response['ResponseMetadata']['HTTPStatusCode'] == 429:
                # Too many concurrent requests in flight
                return None
            else:
                raise Exception(response)

    def invoke_with_result(self, runtime_name, runtime_memory, payload={}):
        """
        Invoke lambda function and wait for result
        """
        function_name = self._format_action_name(runtime_name, runtime_memory)

        response = self.client.invoke(
            FunctionName=function_name,
            Payload=json.dumps(payload)
        )

        return json.loads(response['Payload'].read())

    def get_runtime_key(self, runtime_name, runtime_memory):
        """
        Method that creates and returns the runtime key.
        Runtime keys are used to uniquely identify runtimes within the storage,
        in order to know which runtimes are installed and which not.
        """
        action_name = self._format_action_name(runtime_name, runtime_memory)
        runtime_key = os.path.join(self.name, self.region, self.region, action_name)

        return runtime_key
    
    def _generate_runtime_meta(self, runtime_name):
        """
        Extract preinstalled Python modules from lambda function execution environment
        return : runtime meta dictionary
        """
        action_code = """
        import sys
        import pkgutil

        def main(event, context):
            runtime_meta = dict()
            mods = list(pkgutil.iter_modules())
            runtime_meta['preinstalls'] = [entry for entry in sorted([[mod, is_pkg] for _, mod, is_pkg in mods])]
            python_version = sys.version_info
            runtime_meta['python_ver'] = str(python_version[0])+"."+str(python_version[1])
            return runtime_meta
        """
        action_location = os.path.join(tempfile.gettempdir(), 'extract_preinstalls_aws.py')
        with open(action_location, 'w') as f:
            f.write(textwrap.dedent(action_code))
        
        modules_zip_action = os.path.join(tempfile.gettempdir(), 'extract_preinstalls_aws.zip')
        with zipfile.ZipFile(modules_zip_action, 'w') as extract_modules_zip:
            extract_modules_zip.write(action_location, '__main__.py')
            extract_modules_zip.close()
        with open(modules_zip_action, 'rb') as modules_zip:
            action_bytes = modules_zip.read()

        memory = 192
        try:
            self.client.create_function(
                    FunctionName=self._format_action_name(runtime_name, memory),
                    Runtime=runtime_name,
                    Role=self.role,
                    Handler='__main__.main',
                    Code={
                        'ZipFile': action_bytes
                    },
                    Description=self.package,
                    Timeout=aws_lambda_config.RUNTIME_TIMEOUT_DEFAULT,
                    MemorySize=memory
                )
        except Exception as e:
            raise Exception("Unable to deploy 'modules' action: {}".format(e))
        
        logger.debug("Extracting Python modules list from: {}".format(runtime_name))

        try:
            runtime_meta = self.invoke_with_result(runtime_name, memory)
        except Exception:
            raise Exception("Unable to invoke 'modules' action")
        try:
            self.delete_runtime(runtime_name, memory)
        except Exception:
            raise Exception("Unable to delete 'modules' action")

        if 'preinstalls' not in runtime_meta:
            raise Exception(runtime_meta)

        return runtime_meta
