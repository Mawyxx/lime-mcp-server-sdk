from __future__ import annotations

import pytest

from tests.helpers import generate_rsa_keypair


@pytest.fixture
def rsa_keypair() -> tuple:
    return generate_rsa_keypair()
