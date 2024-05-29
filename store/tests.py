from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client
import tempfile
from .forms import *
from django.conf import settings
from models import *

class TestViews(TestCase):

    def setUp(self):
        user = get_user_model()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        self.user = user.objects.create_user(username="Dmitry")
        self.client1 = Client()
        self.client1.force_login(self.user)
        self.testgender = Gender.objects.create(name="TestGender", slug="TestGender")
        self.testcategory = Category.objects.create(name="TestCategory", slug="TestCategory")
        self.testgender.categories_id.add(self.testcategory)
        photo = (
            b'\x13\x14\x15\x15\x15\x15\x15\x15'

        )
        upl_photo = SimpleUploadedFile(name="testphoto", content=photo)
        self.testproduct = Product.objects.create(name="TestProduct", slug="TestProduct", price=20,
                                                  cat=self.testcategory, gender=self.testgender, price_discount=40,
                                                  discount=True, photo=upl_photo)
        self.testsize = Size.objects.create(name="TestSize")

    def test_main(self):
        response = self.client.get(reverse('main'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context[0].template_name, 'store/main.html')
        self.assertEqual(response.context[0].dicts[3]['gender_selected'], -1)
        self.assertEqual(response.context[0].dicts[3]['cat_selected'], -1)
        self.assertEqual(response.context[0].dicts[3]['ordered'], 0)

    def test_cart(self):
        response = self.client1.get(reverse('cart'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context[0].template_name, 'store/cart.html')
        self.assertEqual(response.context[0].dicts[3]['gender_selected'], -1)
        self.assertEqual(response.context[0].dicts[3]['cat_selected'], -1)
        self.assertEqual(response.context[0].dicts[3]['ordered'], 0)

    def test_cart_redirect(self):
        response = self.client.get(reverse('cart'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/login/')

    def test_liked(self):
        response = self.client1.get(reverse('liked'))
        self.assertEqual(response.context[0].template_name, 'store/liked.html')
        # self.assertTrue(isinstance(response.context[0].dicts[3]['favorite'], Favorite))
        self.assertIsInstance(response.context[0].dicts[3]['favorite'], Favorite)

    def test_liked_redirect(self):
        response = self.client.get(reverse('liked'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/login/')

    def test_register(self):
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'store/register.html')

    def test_login(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'store/login.html')

    def test_logout(self):
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/login/')

    def test_gender(self):
        response = self.client.get(reverse('gender', kwargs={'gender_slug': self.testgender.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'store/gender.html')
        self.assertEqual(response.context[0].dicts[3]['cats'][0].name, 'TestCategory')
        self.assertEqual(response.context[0].dicts[3]['gender_selected'].name, 'TestGender')
        self.assertEqual(response.context[0].dicts[3]['cat_selected'], -1)

    def test_category(self):
        response = self.client.get(
            reverse('category', kwargs={'gender_slug': self.testgender.slug, 'category_slug': self.testcategory.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'store/category.html')
        self.assertEqual(response.context[0].dicts[3]['cats'][0].name, 'TestCategory')
        self.assertEqual(response.context[0].dicts[3]['gender_selected'].name, 'TestGender')
        self.assertEqual(response.context[0].dicts[3]['cat_selected'].name, 'TestCategory')

    def test_add_to_cart(self):
        response = self.client1.get(
            reverse('add_to_cart', kwargs={'product_slug': self.testproduct.slug, 'size_name': self.testsize.name}))
        order = Order.objects.last()
        orderproduct = OrderProduct.objects.last()
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/cart/')
        self.assertEqual(order.user.username, "Dmitry")
        self.assertEqual(orderproduct.product.name, "TestProduct")

    def test_change_quantity_plus(self):
        order_product = OrderProduct.objects.create(user=self.user, product=self.testproduct)
        order_product.save()
        quantity_old = order_product.quantity
        response = self.client1.get(
            reverse('change_quantity', kwargs={'order_product_pk': order_product.pk, 'plus': 1}))
        order_product = OrderProduct.objects.get(pk=order_product.pk)
        quantity_new = order_product.quantity
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/cart/')
        self.assertEqual(quantity_new - quantity_old, 1)

    def test_change_quantity_minus(self):
        order_product = OrderProduct.objects.create(user=self.user, product=self.testproduct, quantity=2)
        order_product.save()
        quantity_old = order_product.quantity
        response = self.client1.get(
            reverse('change_quantity', kwargs={'order_product_pk': order_product.pk, 'plus': 0}))
        order_product = OrderProduct.objects.get(pk=order_product.pk)
        quantity_new = order_product.quantity
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/cart/')
        self.assertEqual(quantity_new - quantity_old, -1)

    def test_change_quantity_delete(self):
        order_product = OrderProduct.objects.create(user=self.user, product=self.testproduct)
        order_product.save()
        response = self.client1.get(
            reverse('change_quantity', kwargs={'order_product_pk': order_product.pk, 'plus': 0}))
        order_product = OrderProduct.objects.filter(pk=order_product.pk)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/cart/')
        self.assertEqual(len(order_product), 0)

    def test_create_checkout_session(self):
        order = Order.objects.create(user=self.user)
        order_product = OrderProduct.objects.create(user=self.user, product=self.testproduct)
        order.products.add(order_product)
        response = self.client1.post(reverse('create-checkout-session', kwargs={'order_id': order.pk}))
        self.assertEqual(response.status_code, 200)

    def test_success_payment(self):
        response = self.client1.get(reverse('success'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context[0].template_name, 'store/successpayment.html')

    def test_cancel_payment(self):
        response = self.client1.get(reverse('cancel'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context[0].template_name, 'store/cancelpayment.html')

    def test_product_landing(self):
        order = Order.objects.create(user=self.user)
        order_product = OrderProduct.objects.create(user=self.user, product=self.testproduct)
        order.products.add(order_product)
        response = self.client1.get(reverse('landing', kwargs={'order_id': order.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context[0].template_name, 'store/checkout.html')
        self.assertEqual(response.context[0].dicts[3]['order_id'], order.pk)

    def test_get_adress(self):
        order = Order.objects.create(user=self.user)
        order.save()
        data = '{"address": "Testadress","city": "city","state": "state","zipcode": "zipcode","order_id": 1}'
        response = self.client1.generic('POST', reverse('get_address'), data)
        order = Order.objects.get(user=self.user)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(order.address.address, "Testadress")
        self.assertEqual(order.address.city, "city")
        self.assertEqual(order.address.state, "state")
        self.assertEqual(order.address.zipcode, "zipcode")

    def test_product(self):
        response = self.client1.get(reverse('product', kwargs={'product_slug': self.testproduct.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context[0].template_name, 'store/product.html')
        self.assertEqual(response.context[0].dicts[3]['product'], self.testproduct)

    def test_add_to_favorite(self):
        response = self.client1.get(
            reverse('add_to_favorite', kwargs={'product_slug': self.testproduct.slug}))
        favorite = Favorite.objects.last()
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/liked/')
        self.assertEqual(favorite.user.username, "Dmitry")
        self.assertEqual(favorite.products.last().name, "TestProduct")

    def test_delete_from_favorite(self):
        favorite = Favorite.objects.create(user=self.user)
        favorite.products.add(self.testproduct)
        favorite.save()
        response = self.client1.get(
            reverse('delete_from_favorite', kwargs={'product_pk': self.testproduct.pk}))
        favorite = Favorite.objects.filter(user=self.user)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/liked/')
        self.assertEqual(favorite[0].products.count(), 0)

    def test_add_to_favorite_redirect(self):
        response = self.client.get(reverse('add_to_favorite', kwargs={'product_slug': self.testproduct.slug}))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/login/')


class TestModels(TestCase):
    @classmethod
    def setUpTestData(cls):
        user = get_user_model()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        user = user.objects.create_user(username="DmitryClient")
        cls.client1 = Client()
        cls.client1.force_login(user)
        User.objects.create(username="Dmitry")
        testgender = Gender.objects.create(name="TestGender", slug="TestGender")
        testcategory = Category.objects.create(name="TestCategory", slug="TestCategory")
        testgender.categories_id.add(testcategory)
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        photo = (b'\x13\x14\x15\x15\x15\x15\x15\x15')
        upl_photo = SimpleUploadedFile(name="testphoto", content=photo)
        product = Product.objects.create(name="TestProduct", slug="TestProduct", price=20, cat=testcategory,
                                         gender=testgender, price_discount=40, discount=True, photo=upl_photo)
        size = Size.objects.create(name="M")
        order_product = OrderProduct.objects.create(user=user, product=product, size=size)
        address = Address.objects.create(state="Minsk", city="Vilyalka", address="Chapaeva", zipcode="253502")
        order = Order.objects.create(user=user, address=address)
        order.products.add(order_product)
        fav = Favorite.objects.create(user=user)
        fav.products.add(product)
        Comment.objects.create(user=user, product=product, text="Description", rating=5)

    def test_user(self):
        user = User.objects.get(username="Dmitry")
        self.assertEqual(user._meta.get_field('middle_name').max_length, 255)
        self.assertEqual(user._meta.get_field('phone_number').max_length, 13)

    def test_product(self):
        user = User.objects.get(username="DmitryClient")
        product = Product.objects.get(pk=1)
        self.assertEqual(product._meta.get_field('name').max_length, 255)
        self.assertEqual(product._meta.get_field('slug').max_length, 255)
        self.assertEqual(product._meta.get_field('discount').default, False)
        self.assertEqual(product._meta.get_field('photo').upload_to, "photos")
        self.assertEqual(product._meta.get_field('availability').max_length, 1)
        self.assertIsInstance(product.cat, Category)
        self.assertIsInstance(product.gender, Gender)
        self.assertEqual(str(product), "TestProduct")
        response = TestModels.client1.get(product.get_add_favorite())
        self.assertRedirects(response, '/liked/')
        response = TestModels.client1.get(product.get_delete_favorite())
        self.assertRedirects(response, '/liked/')
        response = TestModels.client1.get(product.get_absolute_url())
        self.assertEqual(response.status_code, 200)

    def test_category(self):
        cat = Category.objects.get(name="TestCategory")
        gender = Gender.objects.get(name="TestGender")
        self.assertEqual(cat._meta.get_field('name').max_length, 100)
        self.assertEqual(cat._meta.get_field('slug').max_length, 255)
        self.assertEqual(str(cat), "TestCategory")
        response = TestModels.client1.get(cat.get_absolute_url(gender))
        self.assertEqual(response.status_code, 200)

    def test_gender(self):
        gender = Gender.objects.get(name="TestGender")
        self.assertEqual(gender._meta.get_field('name').max_length, 100)
        self.assertEqual(gender._meta.get_field('slug').max_length, 255)
        self.assertIsInstance(gender.categories_id.all()[0], Category)
        self.assertEqual(str(gender), "TestGender")
        response = TestModels.client1.get(gender.get_absolute_url())
        self.assertEqual(response.status_code, 200)

    def test_order_product(self):
        order_product = OrderProduct.objects.get(pk=1)
        self.assertIsInstance(order_product.user, User)
        self.assertIsInstance(order_product.product, Product)
        self.assertIsInstance(order_product.size, Size)
        self.assertEqual(order_product._meta.get_field('ordered').default, False)
        self.assertEqual(order_product._meta.get_field('quantity').default, 1)
        self.assertEquals(order_product.get_total_product_price(), 20)

    def test_order(self):
        order = Order.objects.get(pk=1)
        self.assertIsInstance(order.user, User)
        self.assertIsInstance(order.products.all()[0], OrderProduct)
        self.assertIsInstance(order.address, Address)
        self.assertEqual(order._meta.get_field('ordered').default, False)
        self.assertEqual(str(order), "DmitryClient")
        self.assertEquals(order.get_total_quantity(), 1)
        self.assertEquals(order.get_total(), 20)

    def test_address(self):
        address = Address.objects.get(pk=1)
        self.assertEqual(address._meta.get_field('state').max_length, 100)
        self.assertEqual(address._meta.get_field('city').max_length, 100)
        self.assertEqual(address._meta.get_field('address').max_length, 100)
        self.assertEqual(address._meta.get_field('zipcode').max_length, 100)

    def test_favorite(self):
        fav = Favorite.objects.get(pk=1)
        self.assertIsInstance(fav.user, User)
        self.assertIsInstance(fav.products.all()[0], Product)

    def test_size(self):
        size = Size.objects.get(pk=1)
        self.assertEqual(size._meta.get_field('name').max_length, 5)
        self.assertEqual(str(size), "M")

    def test_comment(self):
        com = Comment.objects.get(pk=1)
        self.assertIsInstance(com.user, User)
        self.assertIsInstance(com.product, Product)
        self.assertEqual(com._meta.get_field("rating").default, 5)
        self.assertEqual(str(com), "DmitryClient - Description")



class TestRegisterUserForm(TestCase):
    def setUp(self):
        self.url = reverse('register')
        self.valid_data = {
            'username': 'testuser',
            'first_name': 'Test',
            'last_name': 'User',
            'middle_name': 'Form',
            'email': 'testuser@example.com',
            'password1': '111qqaa22wwss33eedd',
            'password2': '111qqaa22wwss33eedd',
        }

    def test_register_user_form_valid_data(self):
        form = RegisterUserForm(data=self.valid_data)
        self.assertTrue(form.is_valid())

    def test_register_user_form_required(self):
        invalid_data = self.valid_data.copy()
        invalid_data['username'] = ''
        form = RegisterUserForm(data=invalid_data)
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)
        invalid_data = self.valid_data.copy()
        invalid_data['first_name'] = ''
        form = RegisterUserForm(data=invalid_data)
        self.assertFalse(form.is_valid())
        self.assertIn('first_name', form.errors)
        invalid_data = self.valid_data.copy()
        invalid_data['last_name'] = ''
        form = RegisterUserForm(data=invalid_data)
        self.assertFalse(form.is_valid())
        self.assertIn('last_name', form.errors)
        invalid_data = self.valid_data.copy()
        invalid_data['email'] = ''
        form = RegisterUserForm(data=invalid_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
        invalid_data = self.valid_data.copy()
        invalid_data['password2'] = 'differentpassword'
        form = RegisterUserForm(data=invalid_data)
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)


class TestLoginUserForm(TestCase):
    def setUp(self):
        self.url = reverse('login')
        self.valid_data = {
            'username': 'testuser',
            'password': 'password123',
        }
        self.user = User.objects.create_user(**self.valid_data)

    def test_login_user_form_valid_data(self):
        form = LoginUserForm(data=self.valid_data)
        self.assertTrue(form.is_valid())

    def test_login_user_form_required(self):
        invalid_data = self.valid_data.copy()
        invalid_data['username'] = ''
        form = LoginUserForm(data=invalid_data)
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)
        invalid_data = self.valid_data.copy()
        invalid_data['password'] = ''
        form = LoginUserForm(data=invalid_data)
        self.assertFalse(form.is_valid())
        self.assertIn('password', form.errors)

    def test_login_user_form_invalid_credentials(self):
        invalid_data = self.valid_data.copy()
        invalid_data['password'] = 'wrongpassword'
        form = LoginUserForm(data=invalid_data)
        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors)


class TestCommentForm(TestCase):
    def setUp(self):
        self.valid_data = {
            'rating': 5,
            'text': 'Great product!',
        }

    def test_comment_form_valid_data(self):
        form = CommentForm(data=self.valid_data)
        self.assertTrue(form.is_valid())

    def test_comment_form_required(self):
        invalid_data = self.valid_data.copy()
        invalid_data['rating'] = ''
        form = CommentForm(data=invalid_data)
        self.assertFalse(form.is_valid())
        self.assertIn('rating', form.errors)
        invalid_data = self.valid_data.copy()
        invalid_data['text'] = ''
        form = CommentForm(data=invalid_data)
        self.assertFalse(form.is_valid())
        self.assertIn('text', form.errors)

    def test_comment_form_rating_min_max_value(self):
        invalid_data = self.valid_data.copy()
        invalid_data['rating'] = 0
        form = CommentForm(data=invalid_data)
        self.assertFalse(form.is_valid())
        self.assertIn('rating', form.errors)
        invalid_data = self.valid_data.copy()
        invalid_data['rating'] = 6
        form = CommentForm(data=invalid_data)
        self.assertFalse(form.is_valid())
        self.assertIn('rating', form.errors)
