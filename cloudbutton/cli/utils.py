import shutil
import logging
from cloudbutton.config import CACHE_DIR, STORAGE_FOLDER, \
    default_config, extract_storage_config, extract_compute_config, \
    RUNTIMES_PREFIX, JOBS_PREFIX, DOCKER_FOLDER
from cloudbutton.engine.backends.storage import InternalStorage
from cloudbutton.engine.backends.storage.utils import clean_bucket
from cloudbutton.engine.backends.compute import Compute


logger = logging.getLogger(__name__)


def clean_all(config=None):
    logger.info('Cleaning all Cloudbutton information')
    config = default_config(config)
    storage_config = extract_storage_config(config)
    internal_storage = InternalStorage(storage_config)
    compute_config = extract_compute_config(config)
    compute_handler = Compute(compute_config)

    # Clean localhost executor temp dirs
    shutil.rmtree(STORAGE_FOLDER, ignore_errors=True)
    shutil.rmtree(DOCKER_FOLDER, ignore_errors=True)

    # Clean object storage temp dirs
    compute_handler.delete_all_runtimes()
    sh = internal_storage.storage_handler
    clean_bucket(sh, storage_config['bucket'], RUNTIMES_PREFIX, sleep=1)
    clean_bucket(sh, storage_config['bucket'], JOBS_PREFIX, sleep=1)

    # Clean local cloudbutton cache
    shutil.rmtree(CACHE_DIR, ignore_errors=True)
