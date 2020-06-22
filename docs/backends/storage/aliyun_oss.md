# CloudButton on Alibaba Cloud (Aliyun)

Cloudbutton toolkit with Aliyun Object Storage Service as storage backend.

### Installation

### Configuration

1. Edit your cloudbutton config file and add the following keys:

```yaml
  cloudbutton:
    storage_backend : aliyun_oss

  aliyun_oss:
    public_endpoint : <PUBLIC_ENDPOINT>
    internal_endpoint : <INTRANET_ENDPOINT>
    access_key_id : <ACCESS_KEY_ID>
    access_key_secret : <ACCESS_KEY_SECRET>
```
   - `public_endpoint`: public endpoint (URL) to the service. OSS and FC endpoints are different.
   - `internal_endpoint`: internal endpoint (URL) to the service. Provides cost-free inbound and outbound traffic among services from the same intranet (region).
   - `access_key_id`: Access Key Id.
   - `access_key_secret`: Access Key Secret.
