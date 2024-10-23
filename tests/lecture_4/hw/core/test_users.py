import pytest

from datetime import datetime
from lecture_4.demo_service.core.users import UserInfo, UserRole, UserService, password_is_longer_than_8
from pydantic import SecretStr


def test_password_is_longer_than_8():
    assert password_is_longer_than_8("111") is False
    assert password_is_longer_than_8("111111111") is True


@pytest.fixture
def user_info():
    return UserInfo(username="1234", name="AAA", birthdate=datetime(2003, 8, 16), password=SecretStr("bbbb"))

def test_register(user_info):
    user_service = UserService()
    user_service.register(user_info=user_info)
    assert len(user_service._data) == 1
    assert user_service._last_id == 1
    assert len(user_service._username_index) == 1

def test_register_raises_user_exists_exception(user_info):
    user_service = UserService()
    user_service.register(user_info=user_info)
    with pytest.raises(ValueError):
        user_service.register(user_info=user_info)

def test_register_raises_invalid_password_exception(user_info):
    user_service = UserService(password_validators=[password_is_longer_than_8])
    with pytest.raises(ValueError):
        user_service.register(user_info=user_info)


def test_get_by_username(user_info):
    user_service = UserService()
    user_service.register(user_info=user_info)
    user = user_service.get_by_username("1234")
    assert user_service._data[user_service._username_index["1234"]] == user

def test_get_by_username_returns_none_if_user_doesnt_exist(user_info):
    user_service = UserService()
    user = user_service.get_by_username("1234")
    assert user is None


def test_get_by_id(user_info):
    user_service = UserService()
    user_service.register(user_info=user_info)
    user = user_service.get_by_id(1)
    assert user_service._data.get(1) == user

def test_grant_admin(user_info):
    user_service = UserService()
    user_service.register(user_info=user_info)
    user_service.grant_admin(1)
    assert user_info.role == UserRole.ADMIN
    
def test_grant_admin_raises_user_not_found_error(user_info):
    user_service = UserService()
    with pytest.raises(ValueError):
        user_service.grant_admin(1)

