from django import template
from store.models import *

register = template.Library()

@register.simple_tag(name='getcatsurl')
def get_categoriesURL(gender, cat):
    return reverse('category', kwargs={'category_slug': cat.slug, 'gender_slug': gender.slug})

@register.simple_tag(name='getquantity')
def get_quantity(order_product_pk, plus):
    return reverse('change_quantity', kwargs={'order_product_pk': order_product_pk, 'plus': plus})

#@register.simple_tag(name = 'createorder')
#def create_order(user,product):
    #order.products_id.add(product)
    #order = Order.objects.get_or_create(user=ruser)
