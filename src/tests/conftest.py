"""
Test configuration and fixtures for the Mergington High School API.
Uses mongomock to replace MongoDB with an in-memory database during testing.
"""

import mongomock
import pytest

# Patch MongoDB with an in-memory mock BEFORE the app modules are imported.
# This ensures MongoClient calls in database.py use mongomock automatically.
_mongo_patcher = mongomock.patch(servers=(("localhost", 27017),))
_mongo_patcher.__enter__()

from fastapi.testclient import TestClient  # noqa: E402
import src.backend.database as db_module   # noqa: E402
from src.app import app                    # noqa: E402


@pytest.fixture
def client():
    """Provide a TestClient with a freshly initialized in-memory database."""
    # Drop existing data and re-seed so each test starts from the same state.
    db_module.activities_collection.drop()
    db_module.teachers_collection.drop()
    db_module.init_database()

    with TestClient(app) as test_client:
        yield test_client
