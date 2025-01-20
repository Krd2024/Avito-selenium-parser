# from app_tasks.services.authentication.auth import login_view, register_view
# from app_tasks.views import create_task, main, perform_action
# from django_rest_w.views_rest import TaskSerializerSet
from django.contrib.auth.views import LogoutView
from rest_framework.routers import DefaultRouter
from django.urls import path, include

from drf.views import AvitoSerializerSet

router = DefaultRouter()
router.register(r"add", AvitoSerializerSet, basename="parser")

urlpatterns = []
