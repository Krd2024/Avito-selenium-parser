from rest_framework import serializers
from parsing_app import RequestUser, ResultParsing


class RequestUserSerializer(serializers.ModelSerializer):
    class Meta:
        fields = "__all__"
