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

from app.models import Shop, Category, Product, ProductInfo, Parameter, ProductParameter
from app.serializers import ShopSerializer, ProductSerializer


@api_view(['GET'])
def api_root(request):
    return Response({
        'Просмотр магазинов': reverse('get-shops', request=request),
        'Просмотр товара': reverse('get-products', kwargs={'pk': 1}, request=request),
        'Просмотр категории': reverse('get-category', kwargs={'category': 224}, request=request),
        'Поиск товара': reverse('find-products', request=request) + '?category_id=224&shop_id=1',
        '': '',
        'Update partner info': reverse('load-products', request=request),
        'Swagger': reverse('schema-swagger-ui', request=request),
    })


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


