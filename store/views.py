import stripe
from django.conf import settings
from django.core.mail import send_mail
import json
from django.http import JsonResponse, HttpResponse
from django.template.context_processors import csrf
from django.views import View
from django.views.generic import TemplateView
from django.contrib.auth import logout, login
from django.contrib.auth.views import LoginView
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages

from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView
from stripe.api_resources import charge

from .utils import *
from .models import *
from .forms import *


def main(request):
    products = Product.objects.all()
    context = {
        'products': products,
    }
    context = get_user_context(context, request)
    return render(request, 'store/main.html', context)


def cart(request):
    if not request.user.is_authenticated:
        return redirect("login")

    context = {}
    context = get_user_context(context, request)
    promo_code = request.GET.get('promo_code')

    if 'reset_promo' in request.GET:
        order = context['order']
        order.discount_percent = 0
        order.save()

    if promo_code:
        discount_percent = apply_promo_code(promo_code)
        if discount_percent:
            order = context['order']
            order.discount_percent = discount_percent
            order.save()

    return render(request, 'store/cart.html', context)

def checkout(request):
    context = {}
    context = get_user_context(context,request)
    return render(request, 'store/checkout.html', context)


def liked(request):
    if not request.user.is_authenticated:
        return redirect("login")
    context = {}
    try:
        favorite = Favorite.objects.get(user=request.user)
    except:
        favorite = Favorite.objects.create(user=request.user)
    context['favorite'] = favorite
    context = get_user_context(context,request)
    return render(request, 'store/liked.html', context)


class RegisterUser(CreateView):
    form_class = RegisterUserForm
    template_name = 'store/register.html'
    success_url = reverse_lazy('login')

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        c_def = {"title": "Register"}
        context = get_user_context(context,self.request)
        return dict(list(context.items()) + list(c_def.items()))

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return redirect('main')


class LoginUser(LoginView):
    form_class = LoginUserForm
    template_name = 'store/login.html'

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        c_def = {"title": "Login"}
        context = get_user_context(context,self.request)
        return dict(list(context.items()) + list(c_def.items()))

    def get_success_url(self):
        return reverse_lazy('main')


def logout_user(request):
    logout(request)
    return redirect('login')


def gender(request, gender_slug):
    search_input = request.GET.get('search_area')
    gender = Gender.objects.get(slug=gender_slug)
    cats = gender.categories_id.all()
    if search_input:
        products = Product.objects.filter(gender=gender, name__icontains=search_input)
    else:
        products = Product.objects.filter(gender=gender)
    context = {
            "cats": cats,
            "products": products,
    }
    context = get_user_context(context,request)
    context["gender_selected"] = gender
    return render(request, 'store/gender.html', context)


def category(request, gender_slug,category_slug):
    search_input = request.GET.get('search_area')
    gender = Gender.objects.get(slug=gender_slug)
    cat = Category.objects.get(slug=category_slug)
    cats = gender.categories_id.all()
    if search_input:
        products = Product.objects.filter(gender=gender, cat=cat, name__icontains=search_input)
    else:
        products = Product.objects.filter(gender=gender, cat=cat)
    context = {
            "cats": cats,
            "products" : products,
    }
    context = get_user_context(context,request)
    context["gender_selected"] = gender
    context["cat_selected"] = cat
    return render(request, 'store/category.html', context)


def add_to_cart(request, product_slug,size_name):
    size = Size.objects.get(name=size_name)
    if not request.user.is_authenticated:
        #messages.info(request, "This item was added to your cart.")
        return redirect("login")
    product = Product.objects.get(slug=product_slug)
    order_product, created = OrderProduct.objects.get_or_create(
        product=product,
        user=request.user,
        ordered=False,
        size=size,
    )
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        if order.products.filter(product__slug=product.slug,size=size).exists():
            order_product.quantity += 1
            order_product.save()
            #messages.info(request, "This item quantity was updated.")
            return redirect("cart")
        else:
            order.products.add(order_product)
            return redirect("cart")
    else:
        order = Order.objects.create(user=request.user)
        order.products.add(order_product)
        #messages.info(request, "This item was added to your cart.")
        return redirect("cart")

def change_quantity(request, order_product_pk, plus):
    order_products = OrderProduct.objects.filter(pk=order_product_pk)
    if order_products.exists():
        order_product = order_products[0]
        if plus:
            order_product.quantity += 1
            order_product.save()
        else:
            order_product.quantity -= 1
            if order_product.quantity == 0:
                order_product.delete()
            else:
                order_product.save()
    return redirect("cart")

stripe.api_key = settings.STRIPE_SECRET_KEY

class CreateCheckoutSessionView(View):
    def post(self, request, *args, **kwargs):
        order_id = self.kwargs["order_id"]
        order = Order.objects.get(id=order_id)
        YOUR_DOMAIN = "https://web-production-e5b3.up.railway.app"
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[
                {
                    'price_data': {
                        'currency': 'usd',
                        'unit_amount': order.get_total()*100,#cent
                        'product_data': {
                            'name': "Test Order"#order.name
                        },
                    },
                    'quantity': 1,
                },
            ],
            metadata={
                "order_id": order.id
            },
            mode='payment',
            success_url=YOUR_DOMAIN + '/success/',
            cancel_url=YOUR_DOMAIN + '/cancel/',
        )
        return JsonResponse({
            'id': checkout_session.id
        })


def successPayment(request):
    context = {}
    context = get_user_context(context, request)
    return render(request, "store/successpayment.html",context)

def cancelPayment(request):
    context = {}
    context = get_user_context(context, request)
    return render(request, "store/cancelpayment.html",context)

class ProductLandingPageView(TemplateView):
    template_name = "store/checkout.html"

    def get_context_data(self, **kwargs):
        order_id = self.kwargs["order_id"]
        order = Order.objects.get(pk=order_id)
        context = super(ProductLandingPageView, self).get_context_data(**kwargs)
        context.update({
            "order": order,
            "STRIPE_PUBLIC_KEY": settings.STRIPE_PUBLIC_KEY,
        })
        context.update(csrf(self.request))
        return context

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        # Invalid payload
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return HttpResponse(status=400)

    # Handle the checkout.session.completed event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']

        customer_email = session["customer_details"]["email"]
        order_id = session["metadata"]["order_id"]
        order = Order.objects.get(id=order_id)
        order.ordered = True
        order.save()
        s = "Thanks for your purchase\nYour cart:\n"
        i = 1
        address = order.address
        ss = f"New order\nAddress: state: {address.state} city: {address.city} address: {address.address} zipcode: {address.zipcode}\nCart:\n"

        for order_product in order.products.all():
            order_product.ordered = True
            order_product.save()
            s += f"{i}) {order_product.product.name} Price: {order_product.product.price} Count: {order_product.quantity}\n"
            ss+= f"{i}) {order_product.product.name} Price: {order_product.product.price} Count: {order_product.quantity}\n"
        send_mail(
            "Order confirmation",
            s,
            "store13313@gmail.com",
            [customer_email],
            fail_silently = False,
        )
        send_mail(
            "New Order",
            ss,
            "store13313@gmail.com",
            ["dimonchechulov@gmail.com"],
            fail_silently=False,
        )
    return HttpResponse(status=200)


@csrf_exempt
def get_address(request):
    if request.method == "POST":
        data = json.loads(request.body)
        order = Order.objects.get(pk=data.get("order_id"))
        address = Address.objects.get_or_create(address=data.get('address'),state=data.get('state'),city = data.get('city'),zipcode=data.get('zipcode'))
        order.address = address[0]
        order.save()

        return JsonResponse({"success": True})
    else:
        return JsonResponse({"success": False, "error": "Invalid request method"})

def product(request, product_slug):
    product = Product.objects.get(slug=product_slug)
    comments = product.get_comments()
    form = CommentForm(request.POST or None)
    if form.is_valid() and not request.user.is_authenticated:
        messages.info(request, 'You must log in to your account to leave a review.')
        return redirect('login')

    if form.is_valid():
        comment = form.save(commit=False)
        comment.user = request.user
        comment.product = product
        comment.rating = form.cleaned_data['rating']
        comment.save()
        messages.success(request, 'Your comment was added.')
        return redirect('product', product_slug=product_slug)

    context = {
        'product': product,
        'comments': comments,
        'form': form,
    }
    context = get_user_context(context, request)
    return render(request, 'store/product.html', context)


def add_to_favorite(request,product_slug):
    if not request.user.is_authenticated:
        # messages.info(request, "This item was added to your cart.")
        return redirect("login")
    product = Product.objects.get(slug=product_slug)
    favorite_qs = Favorite.objects.filter(user=request.user)
    if favorite_qs.exists():
        favorite = favorite_qs[0]
        if not favorite.products.filter(slug=product.slug).exists():
            favorite.products.add(product)
            # messages.info(request, "This item quantity was updated.")
        return redirect("liked")

    else:
        favorite = Favorite.objects.create(user=request.user)
        favorite.products.add(product)
        # messages.info(request, "This item was added to your cart.")
        return redirect("liked")

def delete_from_favorite(request,product_pk):
    product = Product.objects.get(pk=product_pk)
    favorite = Favorite.objects.get(user=request.user)
    favorite.products.remove(product)
    return redirect("liked")

def apply_promo_code(promo_code):
    dict_of_codes = {'CLOTHES': 10, 'SUMMER20': 20}
    if promo_code in dict_of_codes:
        return dict_of_codes[promo_code]
    else:
        return None