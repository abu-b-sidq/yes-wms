from django.conf import settings
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import path

from app.api import api
from wms_middleware.admin_views import management_commands_view

admin.site.site_header = "YES WMS Admin"
admin.site.site_title = "YES WMS Admin"
admin.site.index_title = "Warehouse Operations"

urlpatterns = [
    path("admin/management-commands/", admin.site.admin_view(management_commands_view), name="admin_management_commands"),
    path("admin/", admin.site.urls),
    path("api/v1/", api.urls),
]

if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
