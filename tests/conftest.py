import os
import sys
import tempfile
import pytest

# Create a temp DB file and patch DB_PATH BEFORE app is imported so the
# module-level `with app.app_context(): init_db(); seed_db()` block uses it.
_db_fd, _db_path = tempfile.mkstemp(suffix=".db")
os.close(_db_fd)

# Patch the module-level constant before any other import touches it
import database.db as _db_module
_db_module.DB_PATH = _db_path

# Now import the Flask app — the app_context block runs here against _db_path
import app as _flask_app


@pytest.fixture(scope="session")
def app():
    _flask_app.app.config["TESTING"] = True
    yield _flask_app.app
    os.unlink(_db_path)


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def auth_client(client):
    with client.session_transaction() as sess:
        sess["user_id"] = 1
    return client
