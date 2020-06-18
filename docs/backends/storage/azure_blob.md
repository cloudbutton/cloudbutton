# CloudButton on Microsoft Azure

Cloudbutton toolkit with Azure Blob Storage as storage backend.
 
### Configuration

1. Edit your cloudbutton config file and add the following keys:

```yaml
  cloudbutton:
    storage_bucket: <CONTAINER_NAME>
    storage_backend : azure_blob

  azure_blob:
    account_name : <STORAGE_ACCOUNT_NAME>
    account_key : <STORAGE_ACCOUNT_KEY>
```
   - `account_name`: the name of the Storage Account itself.
   - `account_key`: an Account Key, found in *Storage Account* > `account_name` > *Settings* > *Access Keys*.