# Cloudbutton on Openstack Swift

Cloudbutton toolkit with Openstack Swift storage backend.


### Installation

1. Install Openstack Swift and keystone.


### Configuration

2. Edit your cloudbutton config file and add the following keys:

```yaml
    cloudbutton:
        storage_backend: swift

    swift:
        auth_url   : <SWIFT_AUTH_URL>
        region     : <SWIFT_REGION>
        user_id    : <SWIFT_USER_ID>
        project_id : <SWIFT_PROJECT_ID>
        password   : <SWIFT_PASSWORD>
```

- `auth_url`: The keystone endpoint for authenthication.
- `region`: The region of your container
- `user_id`: The user ID
- `project_id`: The Project ID
- `password`: The password
 
