from .executor import FunctionExecutor


def ibm_cf_executor(config=None, runtime=None, runtime_memory=None,
                    workers=None, region=None, storage_backend=None,
                    storage_backend_region=None, rabbitmq_monitor=None,
                    remote_invoker=None, log_level=None):
    """
    Function executor for IBM Cloud Functions
    """
    compute_backend = 'ibm_cf'
    return FunctionExecutor(
        config=config, runtime=runtime, runtime_memory=runtime_memory,
        workers=workers, compute_backend=compute_backend,
        compute_backend_region=region,
        storage_backend=storage_backend,
        storage_backend_region=storage_backend_region,
        rabbitmq_monitor=rabbitmq_monitor,
        remote_invoker=remote_invoker,
        log_level=log_level
    )


def knative_executor(config=None, runtime=None, runtime_memory=None, workers=None,
                     region=None, storage_backend=None, storage_backend_region=None,
                     rabbitmq_monitor=None, remote_invoker=None, log_level=None):
    """
    Function executor for Knative
    """
    compute_backend = 'knative'
    return FunctionExecutor(
        config=config, runtime=runtime, runtime_memory=runtime_memory,
        workers=workers, compute_backend=compute_backend,
        compute_backend_region=region,
        storage_backend=storage_backend,
        storage_backend_region=storage_backend_region,
        rabbitmq_monitor=rabbitmq_monitor,
        remote_invoker=remote_invoker,
        log_level=log_level
    )


def openwhisk_executor(config=None, runtime=None, runtime_memory=None,
                       workers=None, storage_backend=None,
                       storage_backend_region=None, rabbitmq_monitor=None,
                       remote_invoker=None, log_level=None):
    """
    Function executor for OpenWhisk
    """
    compute_backend = 'openwhisk'
    return FunctionExecutor(
        config=config, runtime=runtime, runtime_memory=runtime_memory,
        workers=workers, compute_backend=compute_backend,
        storage_backend=storage_backend,
        storage_backend_region=storage_backend_region,
        rabbitmq_monitor=rabbitmq_monitor,
        remote_invoker=remote_invoker,
        log_level=log_level
    )


def function_executor(config=None, runtime=None, runtime_memory=None,
                      workers=None, backend=None, region=None,
                      storage_backend=None, storage_backend_region=None,
                      rabbitmq_monitor=None, remote_invoker=None, log_level=None):
    """
    Generic function executor
    """
    return FunctionExecutor(
        config=config, runtime=runtime,
        runtime_memory=runtime_memory,
        workers=workers,
        compute_backend=backend,
        compute_backend_region=region,
        storage_backend=storage_backend,
        storage_backend_region=storage_backend_region,
        rabbitmq_monitor=rabbitmq_monitor,
        remote_invoker=remote_invoker,
        log_level=log_level
    )


def local_executor(config=None, workers=None, storage_backend=None,
                   storage_backend_region=None, rabbitmq_monitor=None,
                   log_level=None):
    """
    Localhost function executor
    """
    compute_backend = 'localhost'

    if storage_backend is None:
        storage_backend = 'localhost'

    return FunctionExecutor(
        config=config, workers=workers,
        compute_backend=compute_backend,
        storage_backend=storage_backend,
        storage_backend_region=storage_backend_region,
        rabbitmq_monitor=rabbitmq_monitor,
        log_level=log_level
    )


def docker_executor(config=None, runtime=None, workers=None,
                    storage_backend=None, storage_backend_region=None,
                    rabbitmq_monitor=None, log_level=None):
    """
    Docker function executor
    """
    compute_backend = 'docker'

    if storage_backend is None:
        storage_backend = 'localhost'

    return FunctionExecutor(
        config=config, runtime=runtime,
        workers=workers,
        compute_backend=compute_backend,
        storage_backend=storage_backend,
        storage_backend_region=storage_backend_region,
        rabbitmq_monitor=rabbitmq_monitor,
        remote_invoker=True,
        log_level=log_level
    )
