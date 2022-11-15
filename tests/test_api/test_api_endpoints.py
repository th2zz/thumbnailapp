
from time import sleep

import pytest
from fastapi.testclient import TestClient
from pymongo.collection import Collection
from requests import Response
from starlette import status


def test_health(test_client: TestClient):
    response = test_client.get('/health')
    assert response.status_code == status.HTTP_200_OK


def test_root(test_client: TestClient):
    response: Response = test_client.get("/")
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.celery(broker_url='memory://')
def test_thumbnail_creation(test_client: TestClient, celery_worker, monkeypatch):
    mock_img_url = "https://www.coindesk.com/resizer/WZ459hXE"\
        "xe7zOlA5M4250znguMk=/1056x792/filters:quality(80):"\
        "format(webp)/cloudfront-us-east-1.images.arcpublishi"\
        "ng.com/coindesk/F5AFQN2V2JHUNPYYAAUSSTUDK4.jpg"
    body = {"source_image_url": mock_img_url}
    response = test_client.post('/thumbnail', json=body)
    assert response.status_code == status.HTTP_200_OK
    resp_json: dict = response.json()
    assert "task_id" in resp_json and resp_json["task_id"]
    sleep(3)
    task_id = resp_json["task_id"]

    FAKE_QUERY_RES = {'completed': True, 'source_file_sha256': 'abc',
                      'sha256hex': 'abc', 'base64_thumbnail': 'abc'}
    fake_function = lambda *args, **kwargs: FAKE_QUERY_RES
    monkeypatch.setattr(Collection, "find_one", fake_function)

    response = test_client.get(f'/thumbnail?task_id={task_id}')
    assert response.status_code == status.HTTP_200_OK
    resp_json: dict = response.json()
    assert resp_json['message'] == 'ok'
    assert "task_id" in resp_json and resp_json["task_id"]
    assert "base64_thumbnail_data" in resp_json and resp_json["base64_thumbnail_data"]
    assert "celery_task_status" in resp_json and resp_json["celery_task_status"] == "SUCCESS"
