# Cloudbutton on IBM Cloud Object Storage


Cloudbutton toolkit with IBM COS as storage backend.


### Installation

1. Create an [IBM Cloud Object Storage account](https://www.ibm.com/cloud/object-storage).

2. Crate a bucket in your desired region.

### Configuration

2. Login to IBM Cloud and open up your dashboard. Then navigate to your instance of Object Storage.

3. In the side navigation, click `Endpoints` to find your API endpoint. You must copy both public and private endpoints of the region where you created your bucket.

3. Create the credentials to access to your COS account (Choose one option):
 
#### Option 1 (COS API Key):

4. In the side navigation, click `Service Credentials`.

5. Click `New credential +` and provide the necessary information.

6. Click `Add` to generate service credential.

7. Click `View credentials` and copy the *apikey* value.

8. Edit your cloudbutton config file and add the following keys:
    ```yaml
    cloudbutton:
        storage_backend: ibm_cos
       
    ibm_cos:
       endpoint   : <REGION_ENDPOINT>  
       private_endpoint : <PRIVATE_REGION_ENDPOINT>
       api_key    : <API_KEY>
    ```

#### Option 2 (COS HMAC credentials):

4. In the side navigation, click `Service Credentials`.

5. Click `New credential +`.

6. Click on advanced options and enable `Include HMAC Credential` button. 

7. Click `Add` to generate service credential.

8. Click `View credentials` and copy the *access_key_id* and *secret_access_key* values.

9. Edit your cloudbutton config file and add the following keys:
    ```yaml
    cloudbutton:
        storage_backend: ibm_cos
       
    ibm_cos:
       endpoint   : <REGION_ENDPOINT>  
       private_endpoint : <PRIVATE_REGION_ENDPOINT>
       access_key    : <ACCESS_KEY_ID>
       secret_key    : <SECRET_KEY_ID>
    ```

#### Option 3 (IBM IAM API Key):

4. Navigate to the [IBM IAM dashboard](https://cloud.ibm.com/iam/apikeys)

5. Click `Create an IBM Cloud API Key` and provide the necessary information.

6. Copy the generated IAM API key (You can only see the key the first time you create it, so make sure to copy it).

7. Edit your cloudbutton config file and add the following keys:
    ```yaml
    cloudbutton:
        storage_backend: ibm_cos
        
    ibm:
        iam_api_key: <IAM_API_KEY>
       
    ibm_cos:
        endpoint   : <REGION_ENDPOINT>  
        private_endpoint : <PRIVATE_REGION_ENDPOINT>
    ```

### Summary of configuration keys for IBM Cloud:

|Group|Key|Default|Mandatory|Additional info|
|---|---|---|---|---|
|ibm | iam_api_key | |no | IBM Cloud IAM API key to authenticate against IBM COS and IBM Cloud Functions. Obtain the key [here](https://cloud.ibm.com/iam/apikeys) |


#### Summary of configuration keys for IBM Cloud Object Storage:

|Group|Key|Default|Mandatory|Additional info|
|---|---|---|---|---|
|ibm_cos | endpoint | |yes | Regional endpoint to your COS account. Make sure to use full path with 'https://' as prefix. For example https://s3.us-east.cloud-object-storage.appdomain.cloud |
|ibm_cos | private_endpoint | |no | Private regional endpoint to your COS account. Make sure to use full path. For example: https://s3.private.us-east.cloud-object-storage.appdomain.cloud |
|ibm_cos | api_key | |no | API Key to your COS account. **Mandatory** if no access_key and secret_key. Not needed if using IAM API Key|
|ibm_cos | access_key | |no | HMAC Credentials. **Mandatory** if no api_key. Not needed if using IAM API Key|
|ibm_cos | secret_key | |no | HMAC Credentials. **Mandatory** if no api_key. Not needed if using IAM API Key|

