import pytest
from django.contrib.admin.sites import site
from django.contrib.auth import get_user_model
from django.conf import settings
from django.urls import reverse

from app.documents.models import TransactionDocumentConfig
from app.inventory.models import InventoryBalance, InventoryLedger
from app.masters.models import (
    AppUser,
    Organization,
    Role,
    UserOrgMembership,
)
from app.operations.models import Transaction


pytestmark = pytest.mark.django_db


def test_admin_login_page_is_available(client):
    response = client.get(reverse("admin:login"))

    assert response.status_code == 200
    assert b"csrfmiddlewaretoken" in response.content


def test_admin_index_redirects_anonymous_users_to_login(client):
    response = client.get(reverse("admin:index"))

    assert response.status_code == 302
    assert reverse("admin:login") in response.url


def test_admin_index_loads_for_superuser(client):
    user_model = get_user_model()
    admin_user = user_model.objects.create_superuser(
        username="admin",
        email="admin@example.com",
        password="admin-pass-123",
    )

    client.force_login(admin_user)
    response = client.get(reverse("admin:index"))

    assert response.status_code == 200
    assert b"WMS Masters" in response.content
    assert b"WMS Operations" in response.content
    assert b"WMS Inventory" in response.content
    assert b"WMS Documents" in response.content


def test_admin_registers_key_domain_models():
    expected_models = {
        AppUser,
        InventoryBalance,
        InventoryLedger,
        Organization,
        Role,
        Transaction,
        TransactionDocumentConfig,
        UserOrgMembership,
    }

    assert expected_models <= set(site._registry)


def test_static_root_is_configured_for_admin_assets():
    assert settings.STATIC_ROOT
