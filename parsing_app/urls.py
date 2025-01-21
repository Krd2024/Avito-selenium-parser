# from app_tasks.services.authentication.auth import login_view, register_view
# from app_tasks.views import create_task, main, perform_action
# from django_rest_w.views_rest import TaskSerializerSet
from django.contrib.auth.views import LogoutView
from rest_framework.routers import DefaultRouter
from django.urls import path, include

from parsing_app.drf.views_drf import RequestSerializerSet, ResultParsingSet


router = DefaultRouter()
router.register(r"add", RequestSerializerSet, basename="add")
router.register(r"stat", ResultParsingSet, basename="stat")

add_request = RequestSerializerSet.as_view({"post": "create"})
get_stat = ResultParsingSet.as_view({"get": "list"})

urlpatterns = [
    path("api/v1/add/", add_request, name="add-request"),
    path("api/v1/stat/<request_id>/<start>/<end>/", get_stat, name="get-stat"),
]
# urlpatterns = [path("api/v1/", include(router.urls))]
