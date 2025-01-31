from django.contrib.auth.views import LogoutView
from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import list_view, main, request_user_view, search_view

from parsing_app.drf.views_drf import RequestSerializerSet, ResultParsingSet


router = DefaultRouter()
router.register(r"add", RequestSerializerSet, basename="add")
router.register(r"stat", ResultParsingSet, basename="stat")

add_request = RequestSerializerSet.as_view({"post": "create"})
get_stat = ResultParsingSet.as_view({"post": "create"})

urlpatterns = [
    path("api/v1/add/", add_request, name="add-request"),
    path("api/v1/stat/", get_stat, name="get-stat"),
    #
    path("", main, name="main"),
    path("create/", request_user_view, name="request_user_vies"),
    path("search/", search_view, name="search"),
    path("list/", list_view, name="list"),
]
# urlpatterns = [path("api/v1/", include(router.urls))]
