# Cloudbutton on AWS Lambda

### Installation

1. [Login](https://console.aws.amazon.com/?nc2=h_m_mc) to Amazon Web Services Console (or signup if you don't have an account)
 
2. Navigate to *IAM > Roles*. Click on *Create Role*.
 
3. Select *Lambda* and then click *Next: Permissions*.
 
4. Type `s3` at the search bar and select *AmazonS3FullAccess*. Type `lambda` at the search bar and select *AWSLambdaFullAccess*. Click on *Next: Tags* and then *Next: Review*.
 
5. Type a role name, for example `cloudbutton-execution-role`. Click on *Create Role*.

### Configuration

6. Edit your pywren config file and add the following keys:

```yaml
    cloudbutton:
        compute_backend: aws_lambda

    aws:
        access_key_id : <ACCESS_KEY_ID>
        secret_access_key : <SECRET_ACCESS_KEY>

    aws_lambda:
        execution_role : <EXECUTION_ROLE_ARN>
        region_name : <REGION_NAME>
```

 - `access_key_id` and `secret_access_key`: Account access keys to AWS services. To find them, navigate to *My Security Credentials* and click *Create Access Key* if you don't already have one.
 - `region_name`: Region where the S3 bucket is located and where Lambda functions will be invoked (e.g. `us-east-1`).
 - `execution_role`: ARN of the execution role created at step 2. You can find it in the Role page at the *Roles* list in the *IAM* section (e.g. `arn:aws:iam::1234567890:role/cloudbutton-role`).

### Verify

8. Test if Cloudbutton toolkit on Lambda is working properly:

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
 
