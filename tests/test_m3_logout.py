"""Regression: every shared navigation logout form carries a valid CSRF token."""

import re
import sqlite3
from pathlib import Path

import bcrypt
import pytest

from src.web.app import create_app


@pytest.mark.parametrize(('role', 'path'), [
    ('Requester', '/requests'), ('Requester', '/notifications'),
    ('Staff', '/staff/queue'), ('Manager', '/landing'), ('Administrator', '/landing'),
])
def test_logout_from_shared_navigation(tmp_path, role, path):
    database = str(tmp_path / 'logout.sqlite')
    password = 'p'
    with sqlite3.connect(database) as db:
        db.executescript(Path('src/persistence/schema.sql').read_text())
        db.execute('INSERT INTO users(email,password_hash,role) VALUES (?,?,?)',
                   ('logout@example.test', bcrypt.hashpw(password.encode(), bcrypt.gensalt(10)).decode(), role))
    client = create_app(database, secret_key='x').test_client()
    page = client.get('/login').get_data(as_text=True)
    token = re.search(r'name="csrf_token" value="([^"]+)"', page).group(1)
    assert client.post('/login', data={'email': 'logout@example.test', 'password': password,
                                     'csrf_token': token}).status_code == 302
    page = client.get(path)
    assert page.status_code == 200
    token = re.search(r'name="csrf_token" value="([^"]+)"', page.get_data(as_text=True)).group(1)
    assert client.post('/logout', data={'csrf_token': token}).status_code == 302
    assert client.get(path).status_code == 302
