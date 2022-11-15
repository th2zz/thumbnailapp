import datetime
import os

from celery import Celery

from app.constants import (MONOGO_DB_NAME, TASKS_COLLECTION_NAME,
                           THUMBNAILS_COLLECTION_NAME)
from app.utils import MongoConnector, compute_sha256, get_thumbnail, save_file

CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL",
                                   "redis://localhost:6379")
# CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND",
#                                        "redis://localhost:6379")
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017/")

celery = Celery(__name__)
celery.conf.broker_url = CELERY_BROKER_URL
# celery.conf.result_backend = CELERY_RESULT_BACKEND
MONGO_CLIENT = MongoConnector(MONGO_URL)
TASKS_COLLECTION = MONGO_CLIENT.get_collection(MONOGO_DB_NAME,
                                               TASKS_COLLECTION_NAME)
THUMBNAILS_COLLECTION = MONGO_CLIENT.get_collection(MONOGO_DB_NAME,
                                                    THUMBNAILS_COLLECTION_NAME)


@celery.task(bind=True, name="resize_image")
def resize_image_task(self, source_image_url: str, storage_path: str):
    os.makedirs(storage_path, exist_ok=True)
    downloaded_file = os.path.join(storage_path,
                                   os.path.basename(source_image_url))
    save_file(source_image_url, downloaded_file)
    sha256hex = compute_sha256(downloaded_file)
    # avoid recomputation if possible
    doc = TASKS_COLLECTION.find_one({"source_file_sha256": sha256hex})
    # if there is an entry completed then we can skip, mark current request id as done
    if doc and doc.get("completed", False):
        new_task_info = {"task_id": self.request.id, "source_file_sha256": sha256hex,
                         "completed": True, "last_modify_time": datetime.datetime.now()}
        TASKS_COLLECTION.insert_one(new_task_info)
    else:  # on new task, store thumbnail along with hash in mongo
        doc = THUMBNAILS_COLLECTION.find_one({"source_file_sha256": sha256hex})
        if not doc:
            base64_thumbnail: str = get_thumbnail(downloaded_file)
            now = datetime.datetime.now()
            new_thumbnail_info = {"sha256hex": sha256hex,
                                  "base64_thumbnail": base64_thumbnail, "last_modify_time": now}
            THUMBNAILS_COLLECTION.insert_one(new_thumbnail_info)
        new_task_info = {"task_id": self.request.id, "source_file_sha256": sha256hex,
                         "completed": True, "last_modify_time": now}
        TASKS_COLLECTION.insert_one(new_task_info)
