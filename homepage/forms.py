from django import forms
from .models import Products, Brands, registerUser, Carts, Address, Orders
from django.contrib.auth.forms import UserCreationForm

class ProductForm(forms.ModelForm):
    class Meta:
        model = Products  #the model the form is associated with
        fields = ['productname', 'quantity', 'status', 'brand','image','price','productdescription','category']    
        
     
class BrandForm(forms.ModelForm):
    class Meta:
        model = Brands  #the model the form is associated with
        fields = ['brandname']
        
class Register(forms.ModelForm):
    class Meta:
        model=registerUser
        fields=['name','email','password','confirmpassword']
        widgets = {
            'password': forms.PasswordInput(),
            'confirmpassword': forms.PasswordInput(),
        }
class userLogin(forms.ModelForm):
    class Meta:
        model=registerUser
        fields = ['email', 'password']
        widgets = {
            'password': forms.PasswordInput(),  
        }

class userProfile(forms.ModelForm):
    class Meta:
        model = registerUser
        fields = ['name', 'email','address', 'phone_number']
        
class cartForm(forms.ModelForm):
    class Meta:
        model = Carts
        fields = ['productdetails']
        
class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ['billing_address','billing_city','billing_postcode', 'billing_phonenumber','billing_email',
                  'shipping_address','shipping_city','shipping_postcode','shipping_phonenumber','shipping_email']
        
class OrdersForm(forms.ModelForm):
    class Meta:
        model = Orders
        fields = ['shipping','billing','total','products','quantity', 'status', 'payment_mode', 'discount',
                  'couponcode', 'transaction_id']