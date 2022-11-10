from itertools import islice
from typing import BinaryIO


def read_n_lines(file_opened, N) -> list:
    """ read n lines

    Args:
        file_opened (IO): a file handle
        N (int): how many lines to read

    Returns:
        rows (list): lines read
    """
    rows = []
    for line in islice(file_opened, N):
        rows.append(line)
    return rows


def file_upload_task(file_handle: BinaryIO, storage_path: str, read_batch_size: int):
    """ read the file stream chunk by chunk and write it to local storage path
    without async def, starlette will run it in a separate thread

    Args:
        file_handle (BinaryIO): _description_
        storage_path (str): _description_
        read_batch_size (int): _description_
    """
    with file_handle as input, open(storage_path, 'wb') as output:
        batch = read_n_lines(input, read_batch_size)
        while batch:
            output.writelines(batch)
            batch = read_n_lines(input, read_batch_size)
