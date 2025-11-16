from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    #path('', include("homepage.urls")),
    path('home/', include("homepage.urls")),
    path('admin/', include("custom_admin.urls")),
]
