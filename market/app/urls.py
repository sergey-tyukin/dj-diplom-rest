from django.contrib import admin
from django.urls import path, include
from django.conf.urls import url
from app.views import PartnerUpdate, GetShopsView, GetProductsView, GetCategoryView, \
    FindProductsView, UserView, ContactView, ApiRoot, UserRegister, UserConfirm

from rest_framework.schemas import get_schema_view

from rest_framework import permissions
from drf_yasg.views import get_schema_view as yasg_get_schema_view
from drf_yasg import openapi




schema_view = yasg_get_schema_view(
   openapi.Info(
      title="Snippets API",
      default_version='v1',
      description="Test description",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="contact@snippets.local"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)


urlpatterns = [
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0),
        name='schema-json'),
    url(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    url(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

    path('openapi', get_schema_view(
        title="Market",
        description="Open API description",
        version="1.0.0",
    ), name='openapi-schema'),

    url(r'^$', ApiRoot.as_view(), name='authentication'),


    path('user/register', UserRegister.as_view(), name='user-register'),
    path('user/details', UserView.as_view(), name='user-details'),
    path('user/contacts', ContactView.as_view(), name='user-contacts'),
    path('user/confirm', UserConfirm.as_view(), name='user-confirm'),

    path('shops/get/', GetShopsView.as_view(), name='get-shops'),
    path('products/get/<int:pk>', GetProductsView.as_view(), name='get-products'),
    path('category/get/<int:category>', GetCategoryView.as_view(), name='get-category'),
    path('products/find', FindProductsView.as_view(), name='find-products'),

    # url(r'^products/get/(?P<pk>[0-9]+)/$', GetProductsView.as_view(), name='get-products'),

    path('products/load/', PartnerUpdate.as_view(), name='load-products'),

]
