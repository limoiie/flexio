import os
import pathlib
import tempfile

import pytest as pytest


def case_name(case):
    return case.name


@pytest.fixture(scope='function')
def fake_local_file(tmp_path, faker):
    """
    Path to a fake local file with random content.

    The fake file will be removed after this returned.
    """
    path = pathlib.Path(tempfile.mktemp(dir=tmp_path))
    path.write_text(faker.text())
    yield path
    if os.path.exists(path):
        os.remove(path)
