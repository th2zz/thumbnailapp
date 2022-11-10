import argparse
import os
import uuid
from time import sleep

import requests

parser = argparse.ArgumentParser(description='test client args parser')
parser.add_argument('--url', required=True, type=str)
args = parser.parse_args()

URL = args.url


def main():
    print(f"input argument: url={URL}")
    print("start testing ...")
    test_client = requests
    file_name = str(uuid.uuid4())
    random_content = str(uuid.uuid4())
    current_file_parent_dir = os.path.dirname(__file__)
    mock_files_dir = os.path.join(current_file_parent_dir, 'mock_files')
    os.makedirs(mock_files_dir, exist_ok=True)
    mock_file_path = os.path.join(mock_files_dir, file_name)
    with open(mock_file_path, "w") as f:
        f.write(random_content)
    # test upload download
    files = {'file': (file_name, open(mock_file_path, 'rb'),
                      'multipart/form-data')}
    data = {"Button": "Submit"}
    response = test_client.post(os.path.join(
                                URL, 'files/'),
                                files=files, data=data)
    assert response.status_code == 202
    resp_json = response.json()
    assert resp_json == {"message": f"{file_name} upload task submitted."}
    sleep(3)
    # test download: compare content with generated random content
    response = test_client.get(os.path.join(URL, 'files', file_name))
    assert response.status_code == 200
    print("uploaded file name: ", file_name)
    print("uploaded file content:", random_content)
    print("downloaded file content:", response.text)
    assert response.text == random_content
    # delete all mock files locally
    for _, _, files in os.walk(mock_files_dir):
        for file in files:
            mock_file = os.path.join(mock_files_dir, file)
            os.remove(mock_file)
    print("test finished! No errors on screen means passed!")


if __name__ == "__main__":
    main()
