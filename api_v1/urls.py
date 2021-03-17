from django.urls import include, path
from rest_framework import routers
from . import views


router = routers.DefaultRouter(trailing_slash=False)
router.register(r'couriers', views.CouriersViewSet)

urlpatterns = [
    path('new_couriers', views.NewCouriers.as_view()),
    path('couriers_old', views.couriers),
    path('', include(router.urls)),
]
