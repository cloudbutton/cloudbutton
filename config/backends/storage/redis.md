# Cloudbutton on Redis

Cloudbutton toolkit with Redis storage backend.


### Installation

1. Install Redis >= 5.

2. Secure your installation by setting a password in the redis configuraion file.


### Configuration

3. Edit your cloudbutton config file and add the following keys:

```yaml
    cloudbutton:
        storage_backend: redis

    redis:
        host : <REDIS_HOST_IP>
        port : <REDIS_HOST_PORT>
        password: <REDIS_PASSWORD>
```

- `host`: The host ip adress where you installed the Redis server.
- `port`: The port where the redis server is listening (default: 6379)
- `password`: The password you set in the Redis configuration file
 
