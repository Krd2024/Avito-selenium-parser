from django.contrib import admin

from parsing_app.models import RequestUser, ResultParsing

# Register your models here.
@admin.register(RequestUser)
class RequestUserAdmin(admin.ModelAdmin):
    list_display=("search_phrase","sity")
    
@admin.register(ResultParsing)
class ResultParsingAdmin(admin.ModelAdmin):
    list_display=("request","ads_count","checked_at")
    
