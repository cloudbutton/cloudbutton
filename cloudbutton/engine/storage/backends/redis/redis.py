import io
import redis
import logging
from cloudbutton.engine.storage.utils import StorageNoSuchKeyError

logger = logging.getLogger(__name__)

class RedisBackend:

    def __init__(self, config, bucket=None, executor_id=None):
        del config['user_agent']
        self.client = redis.StrictRedis(**config)
        self.bucket = bucket or ''

    def get_client(self):
        return self.client

    def put_object(self, bucket_name, key, data):
        """
        Put an object in Redis. Override the object if the key already exists. 
        :param bucket_name: bucket name
        :param key: key of the object.
        :param data: data of the object
        :type data: str/bytes
        :return: None
        """
        if not isinstance(data, (str, bytes, bytearray)):
            raise TypeError(type(data), 'valid types: {}'.format((str, bytes, bytearray)))

        redis_key = self._format_key(bucket_name, key)
        components = redis_key.split('/')

        # NOTE: could use a lua script and add from the lowest
        # to the highest dir and stop when SADD returns 0 since
        # then we can assume higher dirs already exist
        pipeline = self.client.pipeline(False)

        # create parent dirs
        for i in range(1, len(components)-1):
            dir = '/'.join(components[:i]) + '/' 
            pipeline.sadd(dir, components[i] + '/')

        # add file to lowest dir
        dir = '/'.join(components[:-1]) + '/'
        pipeline.sadd(dir, components[-1])

        # set actual key
        pipeline.set(redis_key, data)
        pipeline.execute()


    def get_object(self, bucket_name, key, stream=False, extra_get_args={}):
        """
        Get object from Redis with a key.
        Throws StorageNoSuchKeyError if the given key does not exist.
        :param bucket_name: bucket name
        :param key: key of the object
        :return: Data of the object
        :rtype: str/bytes
        """
        redis_key = self._format_key(bucket_name, key)
        try:
            data = self.client.get(redis_key)
        except redis.exceptions.ResponseError:
            raise StorageNoSuchKeyError(bucket_name, key)

        if data is None:
            raise StorageNoSuchKeyError(bucket_name, key)
        
        if stream:
            return io.BytesIO(data)
        else:
            return data

    def head_object(self, bucket_name, key):
        """
        Head object from Redis with a key. 
        Throws StorageNoSuchKeyError if the given key does not exist.
        :param bucket_name: bucket name
        :param key: key of the object
        :return: Data of the object
        :rtype: dict
        """
        return {}   # TODO

    def delete_object(self, bucket_name, key):
        """
        Delete an object from storage.
        :param bucket_name: bucket name
        :param key: data key
        """
        self.delete_objects(bucket_name, [key])

    def delete_objects(self, bucket_name, key_list):
        """
        Delete a list of objects from storage.
        :param bucket_name: bucket name
        :param key_list: list of keys
        """
        redis_key_list = [self._format_key(bucket_name, k) for k in key_list]

        pipeline = self.client.pipeline(False)
        pipeline.delete(*redis_key_list)

        for full_path in redis_key_list:
            components = full_path.split('/')
            pdir = '/'.join(components[:-1]) + '/'
            pipeline.srem(pdir, components[-1])

        pipeline.execute()

    def head_bucket(self, bucket_name):
        """
        Head bucket from Redis with a name.
        Throws StorageNoSuchKeyError if the given bucket does not exist.
        :param bucket_name: name of the bucket
        :return: metadata of the bucket
        :rtype: dict
        """
        return {}   # TODO

    def bucket_exists(self, bucket_name):
        """
        Returns True if bucket exists in storage.
        Throws StorageNoSuchKeyError if the given bucket does not exist.
        :param bucket_name: name of the bucket
        """
        return bool(self.client.exists(self._format_key(bucket_name, '')))

    def list_objects(self, bucket_name, prefix=None):
        """
        Return a list of objects for the given bucket and prefix.
        :param bucket_name: name of the bucket.
        :param prefix: Prefix to filter object names.
        :return: List of objects in bucket that match the given prefix.
        :rtype: list of dict
        """
        pipeline = self.client.pipeline(False)
        for key in self.list_keys(bucket_name, prefix):
            pipeline.get(self._format_key(bucket_name, key))
        return pipeline.execute()

    def list_keys(self, bucket_name, prefix=None):
        """
        Return a list of keys for the given prefix.
        :param bucket_name: name of the bucket.
        :param prefix: Prefix to filter object names.
        :return: List of keys in bucket that match the given prefix.
        :rtype: list of str
        """
        prefix = prefix or ''
        redis_prefix = self._format_key(bucket_name, prefix)

        pdir = '/'.join(redis_prefix.split('/')[:-1]) + '/'
        dir_keys = [key.decode() for key in self.client.smembers(pdir)]
        key_list = []

        for key in dir_keys:
            full_key = pdir + key
            if full_key.startswith(redis_prefix):
                if full_key.endswith('/'):
                    key_list.extend(self._walk(bucket_name, full_key))
                else:
                    key_list.append(full_key)

        offset = len(bucket_name) + 1
        return [key[offset:] for key in key_list]

        
    def _walk(self, bucket_name, dir_key):
        dir_keys = [key.decode() for key in self.client.smembers(dir_key)]
        key_list = []

        for key in dir_keys:
            full_key = dir_key + key
            if full_key.endswith('/'):
                key_list.extend(self._walk(bucket_name, full_key))
            else:
                key_list.append(full_key)

        return key_list


    def _format_key(self, bucket, key):
        return '/'.join([bucket, key])