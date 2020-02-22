from django.contrib import admin
from django.urls import path, include
from app.views import PartnerUpdate, ShopView, ProductView

urlpatterns = [
    path('products/load/', PartnerUpdate.as_view()),
    path('shops/view/', ShopView.as_view(), name='shops'),
    path('products/view/', ProductView.as_view(), name='products')
]
