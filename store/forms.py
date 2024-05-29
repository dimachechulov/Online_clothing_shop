from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django import forms
from .models import *

class RegisterUserForm(UserCreationForm):
    username = forms.CharField(label='UserName', widget=forms.TextInput(
        attrs={'class': 'lf--input', 'placeholder': 'Username', 'style': 'width: 400px; text-align: center; border: 1px solid black; border-radius: 10px; height: 33px;'}))
    first_name = forms.CharField(label='First Name', widget=forms.TextInput(
        attrs={'class': 'lf--input', 'placeholder': 'First Name', 'style': 'width: 400px; text-align: center; border: 1px solid black; border-radius: 10px; height: 33px;'}))
    last_name = forms.CharField(label='Last Name', widget=forms.TextInput(
        attrs={'class': 'lf--input', 'placeholder': 'Last Name', 'style': 'width: 400px; text-align: center; border: 1px solid black; border-radius: 10px; height: 33px;'}))
    middle_name = forms.CharField(label='Middle Name', required=False, widget=forms.TextInput(
        attrs={'class': 'lf--input', 'placeholder': 'Middle Name(not compulsory)', 'style': 'width: 400px; text-align: center; border: 1px solid black; border-radius: 10px; height: 33px;'}))
    email = forms.EmailField(label='Email', widget=forms.EmailInput(
        attrs={'class': 'lf--input', 'placeholder': 'Email', 'style': 'width: 400px; text-align: center; border: 1px solid black; border-radius: 10px; height: 33px;'}))
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput(
        attrs={'class': 'lf--input', 'placeholder': 'Password', 'style': 'width: 400px; text-align: center; border: 1px solid black; border-radius: 10px; height: 33px;'}))
    password2 = forms.CharField(label='Repeat password', widget=forms.PasswordInput(
        attrs={'class': 'lf--input', 'placeholder': 'Repeat password', 'style': 'width: 400px; text-align: center; border: 1px solid black; border-radius: 10px; height: 33px;'}))

    class Meta:
        model = User
        fields = ('username', 'first_name','last_name','middle_name', 'email', 'password1', 'password2',)


class LoginUserForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'lf--input', 'placeholder': 'Username', 'style': 'width: 400px; text-align: center; border: 1px solid black; border-radius: 10px; height: 33px;'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'lf--input', 'placeholder':'Password', 'style': 'width: 400px; text-align: center; border: 1px solid black; border-radius: 10px; height: 33px;'}))


class CommentForm(forms.ModelForm):
    rating = forms.IntegerField(widget=forms.NumberInput(attrs={'min': '1', 'max': '5', 'step': '1'}), required=True)
    text = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}))

    class Meta:
        model = Comment
        fields = ('rating', 'text')

