from rest_framework import serializers

from parsing_app.models import RequestUser, ResultParsing

# from parsing_app import RequestUser, ResultParsing


class RequestUserSerializer(serializers.ModelSerializer):
    class Meta:
        modal = RequestUser
        fields = "__all__"


class ResultParsingSerializer(serializers.ModelSerializer):
    class Meta:
        modal = ResultParsing
        fields = "__all__"
