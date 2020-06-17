def load_config(config_data=None):
    if 'aws' not in config_data and 'aws_s3' not in config_data:
        raise Exception("'aws' and 'aws_s3' sections are mandatory in the configuration")

    required_parameters_0 = ('access_key_id', 'secret_access_key')
    if not set(required_parameters_0) <= set(config_data['aws']):
        raise Exception("'access_key_id' and 'secret_access_key' are mandatory under 'aws' section")
    
    # Put credential keys to 'aws_s3' dict entry
    config_data['aws_s3'] = {**config_data['aws_s3'], **config_data['aws']}
    
    if 'endpoint' not in config_data['aws_s3']:
        raise Exception("'endpoint' is mandatory under 's3' section")