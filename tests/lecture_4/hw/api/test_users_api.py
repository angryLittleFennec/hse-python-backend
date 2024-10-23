import base64
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
import pytest
import pytest_asyncio

from lecture_4.demo_service.api.main import create_app
from lecture_4.demo_service.api.utils import initialize, requires_author



@pytest.fixture
def user_create_json():
    return {
        "username": "user",
        "name": "XXX",
        "password": "xxxxx1xxxx",
        "birthdate": "2001-01-01"
    }


@pytest.fixture
def user_get_json():
    return {
        'birthdate': '2001-01-01T00:00:00',
        'name': 'XXX',
        'role': 'user',
        'uid': 2,
        'username': 'user',
    }


@pytest.fixture
def user_credentials():
    creds = "user:xxxxx1xxxx"
    return base64.b64encode(creds.encode()).decode()


@pytest.fixture
def admin_credentials():
    creds = "admin:superSecretAdminPassword123"
    return base64.b64encode(creds.encode()).decode()


@pytest.fixture
def wrong_credentials():
    creds = "admin:superSecretWrongAdminPassword123"
    return base64.b64encode(creds.encode()).decode()


@pytest_asyncio.fixture
async def client():
    app = create_app()
    async with initialize(app):
        transport = ASGITransport(app=app, raise_app_exceptions=False)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac


@pytest_asyncio.fixture()
async def user(client, user_create_json):
    response = await client.post("/user-register", json=user_create_json)
    return response.json()


@pytest_asyncio.fixture
async def user_id(user):
    return user["uid"]


@pytest_asyncio.fixture
async def username(user):
    return user["username"]


@pytest.mark.anyio
async def test_register_user(client, user_create_json, user_get_json):
    response = await client.post("/user-register", json=user_create_json)
    assert response.json() == user_get_json


@pytest.mark.anyio
async def test_get_user_by_id(client, admin_credentials, user_id, user_get_json):    
    response = await client.post(f"user-get?id={user_id}", headers={"Authorization": f"Basic {admin_credentials}"})
    assert response.status_code == 200
    assert response.json() == user_get_json


@pytest.mark.anyio
async def test_get_user_by_username(client, admin_credentials, username, user_get_json):    
    response = await client.post(f"user-get?username={username}", headers={"Authorization": f"Basic {admin_credentials}"})
    assert response.status_code == 200
    assert response.json() == user_get_json


@pytest.mark.anyio
async def test_user_promote(client, admin_credentials, user_id):
    response = await client.post(f"/user-promote?id={user_id}", headers={"Authorization": f"Basic {admin_credentials}"})
    assert response.status_code == 200
    response = await client.post(f"user-get?id={user_id}", headers={"Authorization": f"Basic {admin_credentials}"})
    assert response.status_code == 200
    assert response.json()["role"] == "admin"


@pytest.mark.anyio
async def test_get_user_without_id_or_username(client, admin_credentials):
    response = await client.post(f"user-get", headers={"Authorization": f"Basic {admin_credentials}"})
    assert response.status_code == 400


@pytest.mark.anyio
async def test_get_user_with_id_and_username(client, admin_credentials, user_id, username):
    response = await client.post(f"user-get?id={user_id}&username={username}", headers={"Authorization": f"Basic {admin_credentials}"})
    assert response.status_code == 400

@pytest.mark.anyio
async def test_get_not_existing_user(client, admin_credentials):
    response = await client.post(f"user-get?id=12345", headers={"Authorization": f"Basic {admin_credentials}"})
    assert response.status_code == 404

@pytest.mark.anyio
async def test_requires_author(client, wrong_credentials, user_id):
    response = await client.post(f"user-get?id={user_id}", headers={"Authorization": f"Basic {wrong_credentials}"})
    assert response.status_code == 401


@pytest.mark.anyio
async def test_requires_admin(client, user_credentials, user_id):
    response = await client.post(f"/user-promote?id={user_id}", headers={"Authorization": f"Basic {user_credentials}"})
    assert response.status_code == 403
