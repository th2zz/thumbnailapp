# coding=utf-8

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def test_client() -> TestClient:
    return TestClient(app)


@pytest.fixture(scope='session')
def celery_config():
    return {
        'broker_url': 'memory://',
        # 'result_backend': 'redis://'
    }
