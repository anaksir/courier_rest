from django.urls import include, path
from rest_framework import routers
from slasty.api_v1 import views


router = routers.DefaultRouter(trailing_slash=False)
router.register(r'couriers', views.CouriersViewSet)

urlpatterns = [
    path('couriers_old', views.couriers),
    path('', include(router.urls)),
]
