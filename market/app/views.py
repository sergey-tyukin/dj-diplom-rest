import json

from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from drf_yasg import openapi
from requests import get
from yaml import load as load_yaml, Loader
from django.views.decorators.csrf import csrf_exempt
from django.core.validators import URLValidator
from django.http import JsonResponse
from django.db import transaction

from rest_framework import generics, permissions
from rest_framework.exceptions import ValidationError
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, UpdateAPIView
from rest_framework.response import Response
from rest_framework.reverse import reverse

from drf_yasg.utils import swagger_auto_schema
from app.models import Shop, Category, Product, ProductInfo, Parameter, ProductParameter, User, \
    Contact, ConfirmEmailToken, Order, OrderItem
from app.serializers import ShopSerializer, ProductSerializer, UserSerializer, ContactSerializer, \
    ConfirmEmailTokenSerializer, OrderItemSerializer


##########
# Точка входа в API
##########

class ApiRoot(APIView):
    swagger_schema = None

    def get(self, request):
        return Response({
            'Регистрация пользователя': reverse('user-register', request=request),
            'Подтверждение e-mail': reverse('user-confirm', request=request),
            'Получение контактов': reverse('user-contacts', request=request),
            'Получение информации по пользователю': reverse('user-details', request=request),
            '-1': '-',
            'Просмотр магазинов': reverse('get-shops', request=request),
            'Поиск товара': reverse('find-products',
                                    request=request) + '?category_id=224&shop_id=1',
            'Работа с корзиной': reverse('basket', request=request),
            '-2': '-',
            'Загрузка товаров': reverse('load-products', request=request),
            '-3': '-',
            'Swagger': reverse('schema-swagger-ui', request=request),
            'Authentication': reverse('authentication', request=request),
            # '': reverse('', request=request),
            'Просмотр товара': reverse('get-products', kwargs={'pk': 1}, request=request),
            'Просмотр категории': reverse('get-category', kwargs={'category': 224},
                                          request=request),

        })


##########
# Работа с пользователями
##########

class UserRegister(APIView):

    def post(self, request, *args, **kwargs):
        """
        Регистрация пользователя

        Регистрация пользователя
        """
        user_serializer = UserSerializer(data=request.data)

        if user_serializer.is_valid():
            with transaction.atomic():
                user = user_serializer.save()
                user.set_password(request.data['password'])
                user.save()

                token, _ = ConfirmEmailToken.objects.get_or_create(user_id=user.id)

                msg = EmailMultiAlternatives("Confirmation Email from Online Market",
                                             f"Your comfirmation token is: {token.key}",
                                             settings.EMAIL_HOST_USER, [user.email])
                # msg.send()

            return JsonResponse({'Status': True})
        else:
            return JsonResponse({'Status': False, 'Errors': user_serializer.errors})


class UserConfirm(APIView):

    def post(self, request, *args, **kwags):
        """
        Подтверждение email пользователя

        Подтверждение email пользователя
        """
        requested_user = request.user

        if requested_user.is_active:
            return JsonResponse({'Status': False, 'Error': 'User is already activated'})

        token = ConfirmEmailToken.objects.filter(
            user=requested_user,
            key=request.data['token']).first()

        if not token:
            return JsonResponse({'Status': False, 'Error': 'Token is invalid'})

        with transaction.atomic():
            token.user.is_active = True
            token.user.save()
            token.delete()
            return JsonResponse({'Status': True})

        return JsonResponse({'Status': False, 'Error': 'Unknown error'})


class UserView(APIView):
    """
    Просмотр и редактирование информации о пользователе
    """
    queryset = User.objects.all()
    # permission_classes = (permissions.IsAuthenticated,)

    @swagger_auto_schema(responses={200: 'Данные успешно извлечены'})
    def get(self, request, *args, **kwargs):
        """
        Просмотр подробной информации о пользователе

        Просмотр подробной информации о пользователе
        """
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        """
        Редактирование информации о пользователе

        Редактирование информации о пользователе
        """
        user_serializer = UserSerializer(request.user, data=request.data, partial=True)
        if user_serializer.is_valid():
            user_serializer.save()
            return JsonResponse({'Status': True})
        else:
            return JsonResponse({'Status': False, 'Errors': user_serializer.errors})


class ContactView(APIView):
    """
    Работа с контактными данными пользователя
    """
    queryset = Contact.objects.all()
    # permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        """
        Получение списка контактных данных

        Получение списка контактных данных
        """
        contacts = Contact.objects.filter(user=request.user.id)
        serializer = ContactSerializer(contacts, many=True)
        return Response(serializer.data)

    def post(self, request):
        """
        Создание новых контактных данных

        Создание новых контактных данных
        """
        request.data.update({'user': request.user.id})
        contact_serializer = ContactSerializer(data=request.data, partial=True)
        if contact_serializer.is_valid():
            contact_serializer.save()
            return JsonResponse({'Status': True})
        else:
            return JsonResponse({'Status': False, 'Errors': contact_serializer.errors})

    def put(self, request):
        """
        Обновление контактных данных

        Обновление контактных данных
        """
        contact_id = request.data['id']
        if not contact_id:
            return JsonResponse({'Status': False, 'Errors': 'Contact ID not found'})

        contact_serializer = ContactSerializer(data=request.data, partial=True)
        if not contact_serializer.is_valid():
            return JsonResponse({'Status': False, 'Errors': contact_serializer.errors})

        contact = Contact.objects.filter(pk=contact_id, user=request.user.id)
        if not contact:
            return JsonResponse({'Status': False, 'Errors': 'Contact not found'})

        for key, field in contact_serializer.validated_data.items():
            contact.update(**{key: field})

        return JsonResponse({'Status': True})

    @csrf_exempt
    def delete(self, request):
        """
        Удаление контактных данных

        Удаление контактных данных
        """
        if not (contacts_ids := request.data.get('items')):
            return JsonResponse({'Status': False, 'Errors': 'Field "items" is not set'})

        try:
            parsed_contact_ids = [int(x) for x in contacts_ids.split(',')]
        except ValueError:
            return JsonResponse({'Status': False, 'Errors': 'Format of "items"\'s  is incorrect'})

        for item in parsed_contact_ids:
            Contact.objects.filter(pk=item, user=request.user.id).delete()

        return JsonResponse({'Status': True})


##########
# Работа с магазином
##########

class GetShopsView(ListAPIView):
    """
    Просмотра списка магазинов

    Просмотра списка магазинов
    """
    queryset = Shop.objects.all()
    serializer_class = ShopSerializer
    # permission_classes = (permissions.IsAuthenticated,)


class BasketView(APIView):
    # permission_classes = (permissions.IsAuthenticated,)
    queryset = Order.objects.all()

    @csrf_exempt
    def post(self, request, *args, **kwags):
        """
        Добавить товары в корзину

        Добавить товары в корзину
        """
        try:
            basket_items = json.loads(request.data.get('items'))
        except ValueError:
            return JsonResponse({'Status': False, 'Errors': 'Запрос составлен некорректно'})

        basket, _ = Order.objects.get_or_create(user_id=request.user.id, state='basket')

        for item in basket_items:
            item.update({'order': basket.id})
            basket_serializer = OrderItemSerializer(data=item)
            if basket_serializer.is_valid():
                basket_serializer.save()
            else:
                return JsonResponse({'Status': False, 'Errors': basket_serializer.errors})

        return JsonResponse({'Status': True})

    def put(self, request, *args, **kwags):
        """
        Редактировать содержимое корзины

        Редактировать содержимое корзины
        """
        try:
            basket_items = json.loads(request.data.get('items'))
        except ValueError:
            return JsonResponse({'Status': False, 'Errors': 'Запрос составлен некорректно'})

        updated_items = []
        unupdated_items = []

        for item in basket_items:
            if isinstance(item['product_info'], int) and isinstance(item['quantity'], int):
                try:
                    product = ProductInfo.objects.get(product__id=item['product_info'])

                    OrderItem.objects.filter(order__user=request.user,
                                          order__state='basket',
                                          product_info=product
                                          ).update(quantity=item['quantity'])

                except:
                    unupdated_items.append(item)
                else:
                    updated_items.append(item['product_info'])
            else:
                unupdated_items.append(item)

        return JsonResponse(
            {'Updated items': str(updated_items), 'Unupdated items': str(unupdated_items)})

    def delete(self, request, *args, **kwags):
        """
        Удалить товары из корзины

        Удалить товары из корзины
        """
        try:
            delete_items = [int(x) for x in request.data.get('items').split(',')]
        except ValueError:
            return JsonResponse({'Status': False, 'Errors': 'Запрос составлен некорректно'})
        deleted_items = []
        undeleted_items = {}
        for item in delete_items:
            try:
                OrderItem.objects.get(order__user=request.user,
                                      order__state='basket',
                                      pk=item).delete()
            except Exception as e:
                undeleted_items[item] = e.args[0]
            else:
                deleted_items.append(item)

        return JsonResponse({'Deleted items': str(deleted_items), 'Undeleted items': str(undeleted_items)})

    def get(self, request, *args, **kwags):
        """
        Получить содержимое корзины

        Получить содержимое корзины
        """
        items = OrderItem.objects.filter(order__user=request.user, order__state='basket')
        items_serializer = OrderItemSerializer(items, many=True)

        return Response(items_serializer.data)


class GetProductsView(generics.RetrieveAPIView):
    """
    Просмотр детальной информации о продукте

    Просмотр детальной информации о продукте
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    # permission_classes = (permissions.IsAuthenticated,)


class FindProductsView(generics.ListAPIView):
    """
    Поиск товара по параметрам

    Поиск товара по параметрам:
     * Категория
     * Магазин
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    # permission_classes = (permissions.IsAuthenticated,)
    lookup_field = 'category'

    def get_queryset(self):
        products = Product.objects.all()

        if category := self.request.GET.get('category_id'):
            products = products.filter(category=category)

        if shop := self.request.GET.get('shop_id'):
            products = products.filter(product_infos__shop__pk=shop)

        return products


##########
# Работа с партнерами
##########

class PartnerUpdate(APIView):
    """
    Обновление прайса магазином

    Обновление прайса магазином
    """

    # permission_classes = (permissions.IsAuthenticated,)

    # @csrf_exempt
    def post(self, request, *args, **kwargs):
        # if not request.user.is_authenticated:
        #     return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        if request.user.type != 'shop':
            return JsonResponse({'Status': False, 'Error': 'Только для магазинов'}, status=403)

        url = request.data.get('url')
        if url:
            validate_url = URLValidator()
            try:
                validate_url(url)
            except ValidationError as e:
                return JsonResponse({'Status': False, 'Error': str(e)})
            else:
                stream = get(url).content

                data = load_yaml(stream, Loader=Loader)

                shop, _ = Shop.objects.get_or_create(name=data['shop'], user_id=request.user.id)
                for category in data['categories']:
                    category_object, _ = Category.objects.get_or_create(id=category['id'], name=category['name'])
                    category_object.shops.add(shop.id)
                    category_object.save()
                ProductInfo.objects.filter(shop_id=shop.id).delete()
                for item in data['goods']:
                    product, _ = Product.objects.get_or_create(name=item['name'], category_id=item['category'])

                    product_info = ProductInfo.objects.create(product_id=product.id,
                                                              external_id=item['id'],
                                                              model=item['model'],
                                                              price=item['price'],
                                                              price_rrc=item['price_rrc'],
                                                              quantity=item['quantity'],
                                                              shop_id=shop.id)
                    for name, value in item['parameters'].items():
                        parameter_object, _ = Parameter.objects.get_or_create(name=name)
                        ProductParameter.objects.create(product_info_id=product_info.id,
                                                        parameter_id=parameter_object.id,
                                                        value=value)

                return JsonResponse({'Status': True})

        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})


##########
# Остальное
##########

class GetCategoryView(generics.ListAPIView):
    """
    List of category

    List of category
    :parameter category: Product identifier
    """
    swagger_schema = None

    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    lookup_field = 'category'
    # permission_classes = (permissions.IsAuthenticated,)
