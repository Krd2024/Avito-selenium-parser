from rest_framework.routers import DefaultRouter
from django.urls import path

from parsing_app.drf.views_drf import RequestSerializerSet, ResultParsingSet
from .views import list_view, main, request_user_view, search_view, request_results_view


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
    path("results/<int:request_id>/", request_results_view, name="request_results"),
]
