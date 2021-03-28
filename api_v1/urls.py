from django.urls import include, path
from rest_framework import routers
from . import views


router = routers.DefaultRouter(trailing_slash=False)
router.register(r'couriers', views.CouriersViewSet, basename='couriers')
router.register(r'orders', views.OrdersViewSet, basename='orders')

urlpatterns = [
    path('', include(router.urls)),
]

print(urlpatterns)