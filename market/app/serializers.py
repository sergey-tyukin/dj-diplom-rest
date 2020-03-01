from rest_framework import serializers
from app.models import Shop, Product, ProductInfo


class ShopSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = ('id', 'name', 'url', 'user', 'state',)


class ProductInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductInfo
        fields = ('model', 'external_id', 'shop', 'quantity', 'price', 'price_rrc')


class ProductSerializer(serializers.ModelSerializer):
    product_infos = ProductInfoSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = ('id', 'name', 'category', 'product_infos')
