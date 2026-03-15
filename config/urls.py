from django.contrib import admin
from django.urls import path, include
from django.views.generic.base import RedirectView

urlpatterns = [
    path("", RedirectView.as_view(url="/api/select-tickers/", permanent=False)),
    path("admin/", admin.site.urls),
    path("api/agent/", include("agent.urls")),
    path("api/", include("market.urls")),
]
