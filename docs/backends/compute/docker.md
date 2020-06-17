# Cloudbutton on Docker

Cloudbutton toolkit with *Docker* as compute backend. Cloudbutton can run functions inside a dokcer container either in the localhost or in a remote host. Currently, IBM Cloud Functions and Knative containers are compatible with this mode of execution.


### Installation

1. [Install the Docker CE version](https://docs.docker.com/get-docker/) in your localhost and in the remote host if you plan to run functions remotely.


### Configuration

#### Option 1 (Localhost):

3. Edit your pywren config file and add the following keys:

   ```yaml
   pywren:
       compute_backend: docker

   docker:
       host: 127.0.0.1
   ```


#### Option 2 (Remote host):

3. Edit your pywren config file and add the following keys:

   ```yaml
   pywren:
       compute_backend: docker

   docker:
       host: <IP_ADDRESS>
       ssh_user: <SSH_USERNAME>
       ssh_password: <SSH_PASSWORD>
   ```

#### Summary of configuration keys for docker:

|Group|Key|Default|Mandatory|Additional info|
|---|---|---|---|---|
|docker | host | localhost |no | IP Address of the host/VM to run the functions |
|docker | ssh_user | |no | SSH username (mandatory for remote host)|
|docker | ssh_password | |no | SSH password (mandatory for remote host)|


### Verify

7. Test if Cloudbutton on Docker is working properly:

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