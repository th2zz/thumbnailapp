# coding: utf8
import hashlib
import io
from base64 import b64encode

import requests
from PIL import Image
from pymongo import MongoClient

from app.constants import DEFAULT_ENCODING, THUMBNAIL_SIZE


class MongoConnector(object):

    _client = None

    def __init__(self, url):
        self.url = url

    def init_client(self):
        if not self._client:
            self._client = MongoClient(self.url)
        return self._client

    def get_db(self, db):
        self.init_client()
        return self.client[db]

    def get_collection(self, db, collection_name):
        self.init_client()
        return self._client[db][collection_name]


def save_file(source_img_url, target_file):
    """ save the file from source url

    Args:
        source_img_url (str): source image url
        target_file (str): target path
    """
    img_data = requests.get(source_img_url).content
    with open(target_file, 'wb') as f:
        f.write(img_data)


def compute_sha256(input_file):
    """ compute sha256 of a file

    Args:
        input_file (str): input file path

    Returns:
        str: sha256 hexidecimal str
    """
    sha256_hash = hashlib.sha256()
    with open(input_file, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    sha256hex: str = sha256_hash.hexdigest()
    return sha256hex


def get_thumbnail(input_file) -> str:
    """ get thumbnail string representation (base64 encoded bytes)

    Args:
        input_file (str): should be an image file

    Returns:
        str: base64 encoded bytes string
    """
    img_bytes = io.BytesIO()
    with Image.open(input_file).convert('RGB') as im:
        im.thumbnail(THUMBNAIL_SIZE)
        im.save(img_bytes, "JPEG")
    bytes_content = img_bytes.getvalue()
    base64_bytes = b64encode(bytes_content)  # encode as base64
    base64_string = base64_bytes.decode(DEFAULT_ENCODING)  # decode as string
    return base64_string
