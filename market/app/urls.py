from django.contrib import admin
from django.urls import path, include
from django.conf.urls import url
from app.views import PartnerUpdate, GetShopsView, GetProductsView, GetCategoryView,\
    FindProductsView, api_root

from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi


schema_view = get_schema_view(
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
    url(r'^$', api_root),

    url(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0),
        name='schema-json'),
    url(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    url(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

    path('shops/get/', GetShopsView.as_view(), name='get-shops'),
    path('products/get/<int:pk>', GetProductsView.as_view(), name='get-products'),
    path('category/get/<int:category>', GetCategoryView.as_view(), name='get-category'),
    path('products/find', FindProductsView.as_view(), name='find-products'),



    # url(r'^products/get/(?P<pk>[0-9]+)/$', GetProductsView.as_view(), name='get-products'),

    path('products/load/', PartnerUpdate.as_view(), name='load-products'),

]
