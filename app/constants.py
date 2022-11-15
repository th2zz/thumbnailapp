import os

DEFAULT_STORAGE_DIR = os.path.join("/tmp", "thumbnail_app_data")
DEFAULT_READ_BATCH_SIZE = 100000
SUPPORTED_IMG_EXTENSIONS = ["jpg", "jpeg", "png", "tiff"]
THUMBNAIL_SIZE = 100, 100
DEFAULT_ENCODING = 'utf-8'
MONOGO_DB_NAME = 'workerdb'
TASKS_COLLECTION_NAME = 'tasks_info'
THUMBNAILS_COLLECTION_NAME = 'thumbnails'
