import dataclasses
import os
import pathlib
import tempfile
from typing import Any, Tuple

import pytest as pytest


@dataclasses.dataclass
class Raises:
    exc: Any | Tuple[Any]
    kwargs: dict = dataclasses.field(default_factory=dict)


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
