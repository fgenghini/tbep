import asyncio

import pytest


@pytest.fixture
def run_async():
    return asyncio.run
