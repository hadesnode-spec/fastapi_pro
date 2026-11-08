from datetime import datetime as RealDateTime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db, get_redis
from app.main import app
from app.models import User, Product
from app.security import hash_password


class FakeRedis:
    def __init__(self):
        self.data = {}

    def set(self, name, value, ex=None):
        self.data[name] = value
        return True

    def exists(self, name):
        return int(name in self.data)

    def delete(self, name):
        return int(self.data.pop(name, None) is not None)


class SQLiteDateTime(RealDateTime):
    @classmethod
    def now(cls, tz=None):
        value = RealDateTime.now(tz)
        if tz is not None:
            return value.replace(tzinfo=None)
        return value


@pytest.fixture(autouse=True)
def patch_auth_datetime(monkeypatch):
    import app.routers.auth as auth

    monkeypatch.setattr(auth, "datetime", SQLiteDateTime)


@pytest.fixture
def db_engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(bind=engine)

    yield engine

    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def db_session(db_engine):
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=db_engine,
    )

    session = TestingSessionLocal()

    yield session

    session.close()


@pytest.fixture
def fake_redis():
    return FakeRedis()


@pytest.fixture
def client(db_session, fake_redis):
    def override_get_db():
        yield db_session

    def override_get_redis():
        return fake_redis

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis] = override_get_redis

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def user(db_session):
    new_user = User(
        name="Test User",
        email="test@example.com",
        password_hash=hash_password("Test@12345"),
        is_active=True,
    )

    db_session.add(new_user)
    db_session.commit()
    db_session.refresh(new_user)

    return new_user


@pytest.fixture
def product(db_session, user):
    new_product = Product(
        name="Laptop",
        description="Test laptop",
        price=65000.00,
        owner_id=user.id,
    )

    db_session.add(new_product)
    db_session.commit()
    db_session.refresh(new_product)

    return new_product