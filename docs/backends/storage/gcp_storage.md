# Cloudbutton on GCP Storage

Cloudbutton toolkit with GCP Storage as storage backend.

### Installation

 1. [Login](https://console.cloud.google.com) to Google Cloud Console (or signup if you don't have an account).
 
 2. Create a new project. Name it `cloudbutton` or similar.
 
 3. Navigate to *IAM & Admin* > *Service Accounts*.
 
 4. Click on *Create Service Account*. Name the service account `cloudbutton-executor` or similar. Then click on *Create*.
 
 6. Add the following roles to the service account:
	 - Service Account User
	 - Cloud Functions Admin
	 - Pub/Sub Admin
	 - Storage Admin

 7. Click on *Continue*. Then, click on *Create key*. Select *JSON* and then *Create*. Download the JSON file to a secure location in you computer. Click *Done*.

 8. Navigate to *Storage* on the menu. Create a bucket and name it `cloudbutton-data` or similar. Remember to update the corresponding Cloudbutton's config field with this bucket name.

### Configuration

9. Edit your cloudbutton config file and add the following keys:

```yaml
    cloudbutton:
        storage_backend: gcp_storage

    gcp:
        project_name : <PROJECT_NAME>
        service_account : <SERVICE_ACCOUNT_EMAIL>
        credentials_path : <FULL_PATH_TO_CREDENTIALS_JSON>
        region : <REGION_NAME>
```

 - `project_name`: Project name introduced in step 2 (e.g. `cloudbutton`)
 - `service_account`: Service account email of the service account created on step 4 (e.g. `cloudbutton-executor@cloudbutton.iam.gserviceaccount.com`)
 - `credentials_path`: **Absolute** path of your JSON key file downloaded in step 7 (e.g. `/home/myuser/cloudbutton-invoker1234567890.json`)
 - `region`: Region of the bucket created at step 8. Functions and pub/sub queue will be created in the same region (e.g. `us-east1`)

### Verify

10. Test if Cloudbutton toolkit on Lambda is working properly:

   Run the next command:
   
   ```bash
   $ cloudbutton test
   ```
   
   or run the next Python code:
   
   ```python
   from cloudbutton.engine.executor import FunctionExecutor
   
   def hello_world(name):
       return 'Hello {}!'.format(name)
    
   if __name__ == '__main__':
        cb_exec = FunctionExecutor()
        cb_exec.call_async(hello_world, 'World')
        print("Response from function: ", cb_exec.get_result())
   ```
 
 
 
