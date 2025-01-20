"""
URL configuration for parsing_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin

"""
URL configuration for project_tasks project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from parsing_project import settings

urlpatterns = [
    path("", include("parsing_app.urls")),
    path("admin_ya/", admin.site.urls),
    #  # Генерация схемы OpenAPI
    path("api/v1/schema/", SpectacularAPIView.as_view(), name="schema"),
    # Swagger UI
    path(
        "api/v1/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    # Redoc UI (если нужно)
    path(
        "api/v1/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"
    ),
]
# if settings.DEBUG:
#     import debug_toolbar

#     urlpatterns = [
#         path("__debug__/", include(debug_toolbar.urls)),
#     ] + urlpatterns

# urlpatterns = [
#     path('admin/', admin.site.urls),
# ]
