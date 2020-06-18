import ssl
import json
import time
import logging
import requests
import http.client
import subprocess as sp
import tempfile
from urllib.parse import urlparse


logger = logging.getLogger(__name__)

class FunctionAppClient:

      def __init__(self, config):
            """
            Constructor
            """
            self.resource_group = config['resource_group']
            self.location = config['location']
            self.storage_account = config['account_name']
            self.functions_version = config['functions_version']

      def create_action(self, action_name, memory=None):
            """
            Create and publish an Azure Function App
            """

            logger.debug('Creating function app')
            cmd = 'az functionapp create --name {} --storage-account {} --resource-group {} --os-type Linux \
                  --runtime python --runtime-version 3.6 --functions-version {} --consumption-plan-location {}'\
                  .format(action_name, self.storage_account, self.resource_group, self.functions_version, self.location)
            child = sp.Popen(cmd, shell=True, stdout=sp.PIPE, stderr=sp.PIPE) # silent
            child.wait()
            logger.debug(child.stdout.read().decode())
            logger.error(child.stderr.read().decode())

            time.sleep(40)
            logger.debug('Publishing function app')
            cmd = 'func azure functionapp publish {} --python --no-build'.format(action_name)
            child = sp.Popen(cmd, shell=True, stdout=sp.PIPE, stderr=sp.PIPE) # silent
            child.wait()
            logger.debug(child.stdout.read().decode())
            logger.error(child.stderr.read().decode())

            cmd = 'az storage account show-connection-string --resource-group {} --name {} --query connectionString --output tsv'\
                  .format(self.resource_group, self.storage_account)
            child = sp.Popen(cmd, shell=True, stdout=sp.PIPE, stderr=sp.PIPE)
            child.wait()
            connString = child.stdout.read().decode()
            connString = connString.split('==')[0] + '==' # to get rid of the end of line char(s)
            logger.debug(connString)
            logger.error(child.stderr.read().decode())

            cmd = 'az functionapp config appsettings set --name {} --resource-group {} --settings "AzureWebJobsDashboard={}" "AzureWebJobsStorage={}"'\
                  .format(action_name, self.resource_group, connString, connString)
            child = sp.Popen(cmd, shell=True, stdout=sp.PIPE, stderr=sp.PIPE) # silent
            child.wait()
            logger.debug(child.stdout.read().decode())
            logger.error(child.stderr.read().decode())

      def delete_action(self, action_name):
            """
            Delete an Azure Function App
            """

            logger.debug('Deleting function app')
            cmd = 'az functionapp delete --name {} --resource-group {}'.format(action_name, self.resource_group)
            child = sp.Popen(cmd, shell=True, stdout=sp.PIPE, stderr=sp.PIPE) # silent
            child.wait()
            logger.debug(child.stdout.read().decode())
            logger.error(child.stderr.read().decode())

