from rest_framework import serializers
from app.models import Shop, Product, ProductInfo, User, Contact, ConfirmEmailToken, Order,\
    OrderItem, Category


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = '__all__'


class UserSerializer(serializers.ModelSerializer):
    contacts = ContactSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'is_staff', 'company',
                  'position', 'contacts')


class ConfirmEmailTokenSerializer(serializers.ModelSerializer):

    class Meta:
        model = ConfirmEmailToken
        fields = ('user', 'key')
        # read_only_fields = ('key',)


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


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name', 'shops')


class OrderSerializer(serializers.ModelSerializer):
    # ordered_items = OrderItemCreateSerializer(read_only=True, many=True)

    total_sum = serializers.IntegerField()
    contact = ContactSerializer(read_only=True)

    class Meta:
        model = Order
        fields = ('id', 'user', 'dt', 'state', 'contact', 'ordered_items', 'total_sum')
        read_only_fields = ('id', )


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ('id', 'product_info', 'quantity', 'order',)
        read_only_fields = ('id',)


class OrderSerializer(serializers.ModelSerializer):
    ordered_items = OrderItemSerializer(read_only=True, many=True)

    contact = ContactSerializer(read_only=True)

    class Meta:
        model = Order
        fields = ('id', 'ordered_items', 'state', 'dt', 'contact',)
        read_only_fields = ('id',)
