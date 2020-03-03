from django.http import Http404
from requests import get
from yaml import load as load_yaml, Loader
from django.views.decorators.csrf import csrf_exempt
from django.core.validators import URLValidator
from django.http import JsonResponse

from rest_framework.decorators import api_view
from rest_framework.exceptions import ValidationError
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework import generics
from rest_framework import permissions

from app.models import Shop, Category, Product, ProductInfo, Parameter, ProductParameter, User, \
    Contact
from app.serializers import ShopSerializer, ProductSerializer, UserSerializer, ContactSerializer


@api_view(['GET'])
def api_root(request):
    return Response({
        'Получение информации по пользователю': reverse('user-details', request=request),
        'Получение контактов': reverse('user-contacts', request=request),
        '': '',
        'Просмотр магазинов': reverse('get-shops', request=request),
        'Просмотр товара': reverse('get-products', kwargs={'pk': 1}, request=request),
        'Просмотр категории': reverse('get-category', kwargs={'category': 224}, request=request),
        'Поиск товара': reverse('find-products', request=request) + '?category_id=224&shop_id=1',
        '': '',
        'Загрузка товаров': reverse('load-products', request=request),
        '': '',
        'Swagger': reverse('schema-swagger-ui', request=request),
    })


# Работа с пользователями

class UserView(APIView):
    queryset = User.objects.all()
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        user_serializer = UserSerializer(request.user, data=request.data, partial=True)
        if user_serializer.is_valid():
            user_serializer.save()
            return JsonResponse({'Status': True})
        else:
            return JsonResponse({'Status': False, 'Errors': user_serializer.errors})


class ContactView(APIView):
    queryset = Contact.objects.all()
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        contacts = Contact.objects.filter(user=request.user.id)
        serializer = ContactSerializer(contacts, many=True)
        return Response(serializer.data)

    def post(self, request):
        request.data.update({'user': request.user.id})
        contact_serializer = ContactSerializer(data=request.data, partial=True)
        if contact_serializer.is_valid():
            contact_serializer.save()
            return JsonResponse({'Status': True})
        else:
            return JsonResponse({'Status': False, 'Errors': contact_serializer.errors})

    def put(self, request):
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
        if not (contacts_ids := request.data.get('items')):
            return JsonResponse({'Status': False, 'Errors': 'Field "items" is not set'})

        try:
            parsed_contact_ids = [int(x) for x in contacts_ids.split(',')]
        except ValueError:
            return JsonResponse({'Status': False, 'Errors': 'Format of "items"\'s  is incorrect'})

        for item in parsed_contact_ids:
            Contact.objects.filter(pk=item, user=request.user.id).delete()

        return JsonResponse({'Status': True})



# Работа с магазином

class GetShopsView(ListAPIView):
    """
    Просмотра списка магазинов
    """
    queryset = Shop.objects.all()
    serializer_class = ShopSerializer


class GetProductsView(generics.RetrieveAPIView):
    """
    Просмотр товара
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer


class GetCategoryView(generics.ListAPIView):
    """
    Просмотр категории
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    lookup_field = 'category'


class FindProductsView(generics.ListAPIView):
    """
    Поиск товара по параметрам:
     * Категория
     * Магазин
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    lookup_field = 'category'

    def get_queryset(self):
        products = Product.objects.all()

        if category := self.request.GET.get('category_id'):
            products = products.filter(category=category)

        if shop := self.request.GET.get('shop_id'):
            products = products.filter(product_infos__shop__pk=shop)

        return products


# Работа с партнерами

class PartnerUpdate(APIView):
    """
    Обновление прайса от поставщика
    """
    # @csrf_exempt
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

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



