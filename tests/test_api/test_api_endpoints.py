import os
import pathlib
import uuid

from fastapi.testclient import TestClient
from requests import Response
from starlette import status


def test_health(test_client: TestClient):
    response = test_client.get('/health')
    assert response.status_code == status.HTTP_200_OK


def test_root(test_client: TestClient):
    response: Response = test_client.get("/")
    assert response.status_code == status.HTTP_200_OK


def test_upload_download_task(test_client: TestClient):
    """ This test tests the basic upload download functionality.
    It will first generate 2 uuid string, 1 for file name, 1 for content. Write the temporary file.
    Upload the temporary file. Download the temporary file and compare result. Finally delete all mock files generated

    Args:
        test_client (TestClient): _description_
    """
    file_name = str(uuid.uuid4())
    random_content = str(uuid.uuid4())
    current_file_parent_dir = pathlib.Path(__file__).parent.resolve()
    mock_files_dir = os.path.join(current_file_parent_dir, 'mock_files')
    os.makedirs(mock_files_dir, exist_ok=True)
    mock_file_path = os.path.join(mock_files_dir, file_name)
    with open(mock_file_path, "w") as f:
        f.write(random_content)
    # test upload download
    files = {'file': (file_name, open(mock_file_path, 'rb'),
                      'multipart/form-data')}
    data = {"Button": "Submit"}
    response = test_client.post('/files/', files=files, data=data)
    assert response.status_code == status.HTTP_202_ACCEPTED
    resp_json = response.json()
    assert resp_json == {"message": f"{file_name} upload task submitted."}
    # test download: compare content with generated random content
    response = test_client.get(f'/files/{file_name}')
    assert response.status_code == status.HTTP_200_OK
    assert response.text == random_content
    # delete all mock files locally
    for _, _, files in os.walk(mock_files_dir):
        for file in files:
            mock_file = os.path.join(mock_files_dir, file)
            os.remove(mock_file)
