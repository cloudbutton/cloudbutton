def load_config(config_data=None):
    if 'azure_blob' not in config_data:
        raise Exception("azure_blob section is mandatory in the configuration")

    required_parameters = ('account_name', 'account_key')

    if set(required_parameters) > set(config_data['azure_blob']):
        raise Exception('You must provide {} to access to Azure Blob Storage'.format(required_parameters))

