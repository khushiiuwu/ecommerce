from collections import Counter
from itertools import chain
from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest
from django.http import JsonResponse
from django.urls import reverse
from django.template import Context, loader
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.contrib.sessions.backends.db import SessionStore
from django.contrib.auth.hashers import make_password, check_password
from django.core.mail import send_mail
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q, Count

from custom_admin.models import Contactus
from ecommerce.settings import RAZOR_KEY_ID, RAZOR_KEY_SECRET
from homepage.decorator import user_login_required

from .forms import ProductForm, BrandForm, Register, userLogin, userProfile, cartForm, AddressForm
from .models import Brands, Category, Products, Review, Wishlist, registerUser, Carts, Orders, Address, Coupons
from django.conf import settings
import json, secrets
import razorpay
import random
import string


razorpay_client = razorpay.Client(auth=(settings.RAZOR_KEY_ID, settings.RAZOR_KEY_SECRET))


def add_session(request, email, user_id):
    request.session['email'] = email
    request.session['id'] = user_id
    return email, user_id

def home(request):
    display_products = Products.objects.filter(brand=31).order_by('id')[:3]
    print(display_products)
    return render(request, 'home.html', {"display_products": display_products})

# Create your views here.
def homepage(request):
    products = Products.objects.all()
    for product in products:
        product.brand = brand_name(product.brand)
        product.quantity = qty(product.quantity, product.id)

    return render(request, 'index.html', {'products': products})

@user_login_required
def my_order(request):
    userid = usercheck(request)
    
    orders = Orders.objects.filter(userid=userid).order_by('-id')
    totalprice = 0
    for order in orders:
        productname = order.products
        price = find_product_price(productname)
        print(price)
        addid = order.shipping
        billingaddress, shippingadress = return_address(addid)
        order.billing = billingaddress
        order.shipping = shippingadress
        imglocation = imagelocation(order.products)
        print(imglocation)
        order.img = imglocation
        order.price = price
        total = order.total
        totalprice = totalprice + total
    
    p = Paginator(orders, 5)    
    page_number = request.GET.get('page')
    
    try:
        page_obj = p.get_page(page_number)
    except PageNotAnInteger:
        page_obj = p.page(1)
    except EmptyPage:
        page_obj = p.page(p.num_pages)
            
    page_range1 = p.page_range
        
    return render(request, 'my_order.html', {'orders':page_obj,'page_obj':page_obj, 'page_iterate':page_range1})

def find_product_price(productname):
    product = Products.objects.get(productname = productname)
    return product.price 

def trackorder(request):
    userid = usercheck(request)
    orderid = request.GET['id']
    
    orders = Orders.objects.get(id=orderid, userid=userid)
    productname = orders.products
    print(orders)
    orders.img = imagelocation(productname)
    return render(request,'order_details.html', {'order':orders})

def category_name(category):
    try:
        categories = Category.objects.get(category = category)
        return categories.id
    except Category.DoesNotExist:
        return None

def shop(request):
    
    query = request.GET.get('query')
    categories = countcategory()
    product = Products.objects.all()
 
    if request.GET.get('category') is not None:
        category = request.GET.get('category')
        print("PRINTING CATEGORY IN GET",category)
        catname = category_name(category)
        if catname is not None:
            print("Category Name",catname)
            product = Products.objects.filter(category=catname)
            # return render(request, 'shop.html', {'products': product, 'categories': categories})
    
    if request.GET.get('sortby') is not None:
        sortby = request.GET.get('sortby')
        print(sortby)
        if sortby == "featured":
            product = Products.objects.all()
            # return render(request,'shop.html',{'products':products, 'categories':categories})
        if sortby == "new-items":
            product = Products.objects.all().order_by('-id')
            print("PRINTING NEW ITEMS PRODUCTS",product)
            # return render(request,'shop.html',{'products':products, 'categories':categories})
        if sortby == "best-selling":
            count = find_most_ordered()
            selected_products = [product_name for product_name in count]  # Extracting product names from the counts dictionary
            products = Products.objects.filter(productname__in=selected_products)
            product1 = Products.objects.exclude(productname__in=selected_products)
            product = list(chain(products,product1))
            print("Union",product)
            # return render(request,'shop.html',{'products':products, 'categories':categories})
        if sortby == "lowtohigh":
            product = Products.objects.all().order_by('price')
            print("PRINTING NEW ITEMS PRODUCTS",product)
            # return render(request,'shop.html',{'products':products, 'categories':categories})
        if sortby == "hightolow":
            product = Products.objects.all().order_by('-price')
            print("PRINTING NEW ITEMS PRODUCTS",product)
            # return render(request,'shop.html',{'products':products, 'categories':categories})
        if sortby == "rating":
            product = rating_count() 
            # return render(request,'shop.html',{'products':ratingcount, 'categories':categories})
    if query is not None:
        print("Query",query)
        try:
            product = Products.objects.filter(Q(productname__icontains=query) | Q(productdescription__icontains=query)| Q(color__icontains=query))
            print("In for existing product!")
            # return render(request, 'shop.html', {'products': product, 'categories': categories})
        except Products.DoesNotExist:
            print("Such Product Doesn't Exist!!")
            return render(request,'shop_empty.html')
        
    
    p = Paginator(product, 6)    
    page_number = request.GET.get('page')
    
    try:
        page_obj = p.get_page(page_number)
    except PageNotAnInteger:
        page_obj = p.page(1)
    except EmptyPage:
        page_obj = p.page(p.num_pages)
            
    page_range1 = p.page_range

    return render(request, 'shop.html', {'products': page_obj, 'categories':categories, 'page_obj':page_obj, 'page_iterate':page_range1})

def rating_count():
    #reviews = Review.objects.all().order_by('-star_rating')
    reviews = Review.objects.raw('SELECT *, avg(hr.star_rating) as average_rating FROM ecommerce.homepage_products as hp LEFT JOIN ecommerce.homepage_review as hr ON hp.id = hr.productid GROUP BY hp.id ORDER BY avg(hr.star_rating) DESC')
    return reviews

def find_rating(reviews):
    product_ids = [item[0] for item in reviews]
    star_ratings = [item[1] for item in reviews]
    ratings = {}
    for i in reviews:
        product = i[0]
        products = Products.objects.get(id=product)
        productname = products.productname
    
        rating = i[1]
             

def countcategory():
    categories = Category.objects.all()
    category = []
    for categoryy in categories:
        prodcategory = categoryy.id
        counts = findpresentcategory(prodcategory)
        category.append((categoryy.category, counts))      
    print("New Category",category)
    return category

def find_most_ordered():
    products = Products.objects.all()
    order = []
    for product in products:
        productname = product.productname
        orders = Orders.objects.filter(Q(products__icontains = productname ))
        if not orders:
            pass
        else:
            for ordery in orders:
                productname = ordery.products
                order.append(productname)
    unique, count_list = delete_duplicates_and_count(order) 
    print("COUNT LIST >>-------<<<",count_list) 
    return unique

def delete_duplicates_and_count(lst):
    unique_elements = list(set(lst))
    element_counts = Counter(lst)
    
    return unique_elements, element_counts

def findpresentcategory(prodcategory):
    print("Category ID", prodcategory)
    products = Products.objects.filter(category=prodcategory)
    product_count = products.count()
    print(product_count)
    return product_count            

def qty(qty, id):
    products = Products.objects.get(id=id)
    amt = products.quantity
    if int(qty) > 0 and int(qty) <= amt:
        return qty


def check_cart(product_id, u_id):
    try:
        cart = Carts.objects.get(productdetails=product_id, userid=u_id)
        return cart
    except Carts.DoesNotExist:
        return None


@csrf_exempt
def coupon(request):
    print(request)
    if request.method == "POST":
        coupon_val = request.POST.get('coupon_name')
        print(coupon_val)
        total_amount = request.session['total']
        print(total_amount)
        discounted_amount, total_price = calculate_new_total(total_amount, coupon_val)

        amount = {}
        amount['discounted_amount'] = discounted_amount
        amount['total_amount'] = total_price

        price_total = int(total_price)
        request.session['total_price'] = price_total
        request.session['coupon'] = coupon_val
        print(amount)

    return JsonResponse({"amount": amount})


def calculate_new_total(current_total, coupon_val):
    try:
        coupons = Coupons.objects.filter(couponname=coupon_val)
        if coupons is not None:
            for coupon in coupons:
                discount_type = coupon.type
                print("This is the discount type", discount_type)
                discount_amount = coupon.amount
                curr_total = int(current_total)

                restriction = coupon.restriction
                used_count = coupon.used_count

                if restriction != used_count:
                    if discount_type == "percentage":
                        discount = int(discount_amount)/100
                        total_discount = int(curr_total * discount)
                        total = int(curr_total - total_discount)
                        print(total)
                    else:
                        total_discount = int(discount_amount)
                        total = curr_total - total_discount
                    return total_discount, total
                else:
                    return "Coupon code has been already used."
    except Coupons.DoesNotExist:
        return None
    
def thankyou(request):
    return render(request,'thankyou.html')

def wishlist(request):

    userid = usercheck(request)   

    if request.GET.get('productid') is not None: 
        productid = request.GET.get('productid')
        image  = image_name(productid)
        wishlist = Wishlist()
        wishlist.image = image
        wishlist.productname = productid
        wishlist.userid = userid
        wishlist.save()
        
        wishlists =  Wishlist.objects.filter(userid=userid)
        for wishlist in wishlists:
            product = wishlist.productname
            productname, price, image = product_name(product)
            wishlist.productname = productname
            wishlist.price = price
            
        return render(request, 'wishlist.html',{'wishlists':wishlists})
    try:
        wishlists = Wishlist.objects.filter(userid = userid)
        if not wishlists:
            return  render(request, 'empty_wishlist.html')

        print(wishlists)
        for wishlist in wishlists:
            product = wishlist.productname
            wishlist.productid = wishlist.productname
            productname, price, image = product_name(product)
            wishlist.price = price
            wishlist.productname = productname

        return render(request, 'wishlist.html',{'wishlists':wishlists})
    except Wishlist.DoesNotExist:
        return render(request, 'empty_wishlist.html')
    
def remove_wishlist(request):
    user_id = usercheck(request)
    productid = request.GET.get('productid')
    print("User ID", user_id)
    print(productid)

    wishlist = Wishlist.objects.filter(userid=user_id, productname=productid)
    print(wishlist.count)

    wishlist.delete()
    print("Cart Product Removed Successfully for user", user_id, "and product ->", productid, "!")

    return redirect('wishlist')
    
def image_name(productid):
    product = Products.objects.get(id=productid)
    return product.image
    


@csrf_exempt
def add_cart(request):
    carts = Carts()
    u_id = usercheck(request)
    print(request.POST,"REQUEST",request.GET)
    print(request.POST,"REQUESTS",request.GET)
    
    if request.GET.get('productid') is not None:
        productid = request.GET.get('productid')
        quanty = request.GET.get('quantity')
        carts  = Carts()
        carts.userid = u_id
        carts.productdetails = productid
        carts.qty = quanty
        carts.save()
        
        wishlist = Wishlist.objects.get(productname=productid, userid = u_id)
        wishlist.delete()
        print(wishlist)
        
        return redirect('wishlist')
        
    if request.method == "GET" and request.GET.get('product_id') is not None:
        # To get the values from the url!
        product = request.GET.get('product_id')
        quantity = request.GET.get('qty')

        cart_total = 0

        cart = Carts()

        cart.userid = u_id

        cartlist = check_cart(product, u_id)

        if cartlist is None:
            cart.productdetails = product
            cart.qty = quantity
            cart.save()
        else:
            cart_total = 0
            cartck = Carts.objects.get(productdetails=product, userid=u_id)
            if cartck is not None:
                prodt = cartck.productdetails
                prod_name, price, image = product_name(prodt)

                quantity = int(quantity) + int(cartlist.qty)
                cartck.qty = quantity
                cartck.productdetails = product
                cartck.save()

        carts = Carts.objects.filter(userid=u_id)
        for cart in carts:
            qty = cart.qty
            print(qty)
            prod_name, price, image= product_name(cart.productdetails)
            cart.prod_id = cart.productdetails
            cart.productdetails = prod_name
            cart.img = image
            cart.price = price
            c_total = int(price) * int(qty)
            cart.total = c_total

            cart_total = int(cart_total) + int(c_total)
        print(carts)
        print(u_id)

        request.session['total'] = cart_total

        return render(request, 'add_cart.html', {'carts': carts, 'total': cart_total})
    else:
        print("HERE")
        carts = Carts.objects.filter(userid=u_id)
        if not carts:
            return render(request, "cart_empty.html")

        cart_total = 0
        for cart in carts:
            qty = cart.qty
            print(qty)
            cart.prod_id = cart.productdetails
            prod_name, price, image = product_name(cart.productdetails)
            cart.productdetails = prod_name
            cart.img = image
            cart.price = price
            c_total = int(price) * int(qty)
            cart.total = c_total

            cart_total = int(cart_total) + int(c_total)
            
        request.session['total'] = cart_total

        return render(request, 'add_cart.html', {'carts': carts, 'total': cart_total})
        
    

def remove_cart(request, prod_id):
    user_id = usercheck(request)

    print("User ID", user_id)
    print(prod_id)

    cart = Carts.objects.filter(userid=user_id, productdetails=prod_id)
    print(cart.count)

    cart.delete()
    print("Cart Product Removed Successfully for user",
          user_id, "and product ->", prod_id, "!")

    return redirect('cart')
# ----------------APPEND--CART-------------


def add_qty(request, prod_id):
    user_id = usercheck(request)
    print("Add Qty", prod_id)

    cart_qty = Carts.objects.filter(userid=user_id, productdetails=prod_id)
    print(cart_qty)
    for cart in cart_qty:
        qty = cart.qty
        added_qty = int(qty) + 1
        print(added_qty)

        cart.qty = added_qty
        cart.save()

    return redirect('cart')


def remove_qty(request, prod_id):
    user_id = usercheck(request)
    print("Remove Qty", prod_id)

    cart_qty = Carts.objects.filter(userid=user_id, productdetails=prod_id)
    print(cart_qty)
    for cart in cart_qty:
        qty = cart.qty
        added_qty = int(qty) - 1
        if added_qty >= 1:
            cart.qty = added_qty
            cart.save()
        else:
            print("Quantity Should be at least 1")

    return redirect('cart')
# -----------------------------------------


@csrf_exempt
@user_login_required
def checkout(request):
    if (request.session['email'] == None):
        return redirect('login')

    form = AddressForm()
    print(request.GET)
    productid = request.GET.getlist('prod_id[]', [])
    quantities = request.GET.getlist('quantity[]', [])

    print(productid, quantities)
    prod_dict = []
    productnames = []
    prices = []
    for id, quantity in zip(productid, quantities):
        try:
            product = Products.objects.get(id=id)
            
            productnames.append(product.productname)
            price = product.price
            tp = int(quantity) * int(price)
            prices.append(tp)
            prod_dict.append((product.productname, quantity, tp))

            """print(tp, prices)"""
        except Products.DoesNotExist:
            print("Product with ID", productid, "does not exist")

    print("After loop values", productnames, prices)

    
    total = request.GET.get('total')
   
    
    my_dict = {}

    """for productname, price, quantity in zip(prod_dict['productnames'], prod_dict['prices'], prod_dict['quantities']):
        product_key = f"product{len(my_dict) + 1}"
        product_value = f"{productname}, {quantity}, {price}"
        my_dict[product_key] = product_value

    print(prod_dict)"""
    print("This is my dict")
    print(my_dict)

   
    return render(request, 'checkout.html', {'form': form, 'my_dict': prod_dict, 'total': total })


@csrf_exempt
def savecart(request):
    form = AddressForm()
    user_id = usercheck(request)
    print("This is the userid below!")
    print(user_id)
    if request.method == "POST":
        # form = AddressForm(request.POST)
        print(request)
        billing_address = request.POST["billing_address"]
        billing_city = request.POST["billing_city"]
        billing_email = request.POST["billing_email"]
        billing_phonenumber = request.POST["billing_phonenumber"]
        billing_postcode = request.POST["billing_postcode"]
        shipping_address = request.POST["shipping_address"]
        shipping_city = request.POST["shipping_city"]
        shipping_email = request.POST["shipping_email"]
        shipping_phonenumber = request.POST["shipping_phonenumber"]
        shipping_postcode = request.POST["shipping_postcode"]

        addresses = Address.objects.filter(user_id=user_id)

        if not addresses.exists():
            print("Enter Address!")
            address = Address()
            address.billing_address = billing_address
            address.billing_city = billing_city
            address.billing_email = billing_email
            address.billing_phonenumber = billing_phonenumber
            address.billing_postcode = billing_postcode
            address.shipping_address = shipping_address
            address.shipping_city = shipping_city
            address.shipping_email = shipping_email
            address.shipping_phonenumber = shipping_phonenumber
            address.shipping_postcode = shipping_postcode
            address.user_id = user_id
            address.save()

        #!RAZORPAY-START!
        currency = "INR"
        totalamt = request.session['total']
        amount = totalamt * 100

        couponname = None
        
        print(request.POST)
        if 'coupon' not in request.session or request.session['coupon'] is None:
            print('No coupon!')
            couponname = ""
        else:
            coupon = request.session['coupon']
            coupon_exist = Coupons.objects.filter(couponname=coupon)
            print(coupon_exist)
            totalamt = request.session['total_price']
            print(total_amount)
            amount = totalamt * 100
            couponname = coupon

        # Create a razorpay order
        razorpay_order = razorpay_client.order.create({"amount": int(amount) , "currency": "INR", "payment_capture": "1"})
        # order id of newly created order
        razorpay_order_id = razorpay_order['id']
        callback_url = 'http://127.0.0.1:8000/home/paymenthandler/'

        # store in session
        request.session['razorpay_order_id'] = razorpay_order_id

        # we need to pass these details to frontend
        context = {}
        context['razorpay_order_id'] = razorpay_order_id
        context['razorpay_merchant_key'] = settings.RAZOR_KEY_ID
        context['razorpay_amount'] = amount
        context['currency'] = currency
        context['callback_url'] = callback_url
        context['coupon'] = couponname
        #!RAZORPAY-END!
        print(context)

        # bag.billing_address = form.cleaned_data['billing_address']#bag.billing_city = form.cleaned_data['billing_city']#bag.billing_postcode = form.cleaned_data['billing_postcode']#bag.billing_phonenumber = form.cleaned_data['billing_phonenumber']#bag.billing_email = form.cleaned_data['billing_email']
        # bag.shipping_address = form.cleaned_data['shipping_address']#bag.shipping_city = form.cleaned_data['shipping_city']#bag.shipping_postcode = form.cleaned_data['shipping_postcode']#bag.shipping_phonenumber = form.cleaned_data['shipping_phonenumber']#bag.shipping_email = form.cleaned_data['shipping_email']

        uid = Carts.objects.filter(userid=user_id)
        if uid.exists():
            for cart_item in uid:
                order = Orders()

                usrid = cart_item.userid  # !-userid-!
                prdct = cart_item.productdetails  # !-product-id-!
                # !-product-name-and-price-are-obtained-from-product_name-function-!
                pdtname, price, img = product_name(prdct)
                quanty = cart_item.qty  # !-quantity of the product-!
                total = int(quanty) * int(price)
                product_total = total

                address = find_address_id(usrid)

                order.shipping = address
                order.billing = address

                order.total = product_total
                order.products = pdtname
                order.quantity = quanty

                order.status = "Pending"
                order.payment_mode = ""
                order.discount = 0
                order.couponcode = couponname
                order.transaction_id = ""
                order.userid = user_id
                order.orderid = razorpay_order_id
                order.save()

            # Sends a success response
            return JsonResponse({"context": context})
        else:
            return HttpResponse("Cart Value Missing!")
    else:
        return HttpResponse("Request method is not POST!")


@csrf_exempt
def paymenthandler(request):
    if request.method == "POST":
       
        if "razorpay_signature" in request.POST:
            
            print("pass")
            print(request.POST.get('coupon'))
            if "razorpay_signature" in request.POST:
                # totalamt = request.GET.get('total')
                try:
                    print("pass2")
                    # get the required parameters from post request.
                    payment_id = request.POST.get('razorpay_payment_id', '')
                    razorpay_order_id = request.POST.get('razorpay_order_id', '')
                    signature = request.POST.get('razorpay_signature', '')
                    params_dict = {
                        'razorpay_order_id': razorpay_order_id,
                        'razorpay_payment_id': payment_id,
                        'razorpay_signature': signature
                    }

                    orders = Orders.objects.filter(orderid=razorpay_order_id)
                    print(orders)
                    for order in orders:
                        user_id = order.userid
                        couponname = order.couponcode
                        price = order.total
                        quanty = order.quantity
                        total = int(price) * int(quanty)

                        if couponname != "":
                            discounted_amount, total_price = calculate_new_total(
                                total, couponname)
                            total = total_price
                            print("Coupon discounted total", total)

                    print("This is the user id", user_id)

                    # verify the payment signature.
                    print(request, payment_id)
                    result = razorpay_client.utility.verify_payment_signature(params_dict)
                    print(result)
                    if result:
                        total_amount = total

                        if result is not None:
                            print("pass3")
                            amount = total_amount * 100
                            print(amount)

                            try:
                                print("pass ok")
                                # capture the payemt
                                print(payment_id, amount)

                                # deleting the value of the cart object after placing an order
                                delcartobj = Carts.objects.filter(userid=user_id)
                                delcartobj.delete()

                                if couponname is not None and couponname != "":
                                    couponcount_check = Coupons.objects.filter(
                                        couponname=couponname)
                                    for couponcount in couponcount_check:
                                        count = int(couponcount.used_count)
                                        restricted = couponcount.restriction
                                        usedcount = couponcount.used_count
                                        if restricted != usedcount:
                                            new_count = count+1
                                            couponcount.used_count = new_count
                                            couponcount.save()

                                print("payment captured")
                                # render success page on successful caputre of payment
                                return render(request, 'thankyou.html')
                            except:
                                # if there is an error while capturing payment.
                                return render(request, 'thankyou.html')
                    else:
                            print("fail1")
                            # if signature verification fails.
                            return render(request, 'thankyou.html')
                except:
                    print("fail2")
                    # if we don't find the required parameters in POST data
                    return render(request, 'thankyou.html')
            else:
                    print("fail3")
                # if other than POST request is made.
                    return render(request, 'thankyou.html')
    else:
                print("fail3")
                # if other than POST request is made.
                return render(request, 'thankyou.html')

def total_amount(request):
    user_id = usercheck(request)
    uid = Carts.objects.filter(userid=user_id)

    cart_total = 0
    for cart_item in uid:
        usrid = cart_item.userid  # !-userid-!
        prdct = cart_item.productdetails  # !-product-id-!
        # !-product-name-and-price-are-obtained-from-product_name-function-!
        pdtname, price = product_name(prdct)
        quanty = cart_item.qty  # !-quantity of the product-!
        total = int(quanty) * int(price)
        c_total = int(price) * int(quanty)
        cart_item.total = c_total

        cart_total = int(cart_total) + int(c_total)

    print("This is the total", cart_total)

    return cart_total

@user_login_required
def contact_us(request):
    email = request.session['email']
    print(email)
    user = registerUser.objects.get(email=email)
    username = user.name
    return render(request, 'contact.html', {'email': email, 'username': username})

@csrf_exempt
def savecontactus(request):
    userid = usercheck(request)
    print(request.POST)
    msg = request.POST.get('msg')
    firstname = request.POST.get('firstname')
    email = request.POST.get('email')
    contact = Contactus()
    contact.firstname = firstname
    contact.email = email
    contact.message = msg
    contact.userid = userid
    contact.save()

def about_us(request):
    return render(request, 'aboutus.html')


@csrf_exempt
@login_required(redirect_field_name='user_login')
def order(request):
    u_id = usercheck(request)
    order_id = request.GET.get('orderid')

    orders = Orders.objects.filter(userid=u_id, orderid=order_id)
    totalprice = 0

    if request.method == "GET":
        for order in orders:
            addid = order.shipping
            billingaddress, shippingadress = return_address(addid)
            order.billing = billingaddress
            order.shipping = shippingadress
            total = order.total
            totalprice = totalprice + total

    return render(request, 'order.html', {'orders': orders, 'totalprice': totalprice})


def orderhistory(request):
    u_id = usercheck(request)
    

    orders = Orders.objects.filter(userid=u_id).values('orderid').distinct()
    
        
    return render(request, 'orderhistory.html', {'orders': orders})

def imagelocation(productname):
    product = Products.objects.get(productname=productname)
    return product.image

def return_address(addid):
    address = Address.objects.get(id=addid)
    billingaddress = f"{address.billing_address}, {address.billing_city}, {address.billing_postcode}, {address.billing_phonenumber}, {address.billing_email}"
    print(billingaddress)
    shippingaddress = f"{address.shipping_address}, {address.shipping_city}, {address.shipping_postcode}, {address.shipping_phonenumber}, {address.shipping_email}"
    return billingaddress, shippingaddress


def find_address_id(userid):
    address = Address.objects.get(user_id=userid)
    return address.id


def product_name(product):
    print("PRODUCT ID", product)
    try:
        pdt = Products.objects.get(id=product)
        print(pdt)
        return pdt.productname, pdt.price, pdt.image
    except:
        print("Not correct product id")


def usercheck(request):
    email = request.session['email']
    user = registerUser.objects.get(email=email)
    user_id = user.id
    return user_id

# Create your views here.


def Registeration(request):

    if request.method == 'POST':
        form = Register(request.POST)
        print(form)

        password = form.cleaned_data['password']
        confirmpassword = form.cleaned_data['confirmpassword']
        print(confirmpassword)
        if password == confirmpassword:
            form.save(commit=False)
            form.instance.password = make_password(password)
            form.save()
            return redirect('user_login')
        else:
            messages.error(
                request, 'Password and confirm password do not match.')
    else:
        form = Register()

    return render(request, 'registeration.html', {'form': form, 'login_form': userLogin()})


def login_view(request):
    if 'email' in request.session and request.session['email'] != "":
        print(request.session['email'])

        return redirect('homepage')

    login_form = userLogin()

    if request.method == 'POST':
        login_form = userLogin(request.POST)

        data = request.POST
        password1 = data.get("password", "0")
        email1 = data.get("email", "0")

        user_id, email, password = check_validate(email1, password1)
        # print(check_validate(email1, password1))
        print(user_id)
        if user_id is not None:
            add_session(request, email, user_id)
            return redirect('home')

        else:
            print("having error here")
            messages.error(request, ' Invalid username or password is correct')
            return redirect('user_login')
        # email = login_form.cleaned_data['email']
        # password = login_form.cleaned_data['password']
    #   if user is not None:
    #       login(request, user)
    #       return redirect('ecommerce:homepage/product_list')

    return render(request, 'login_user.html', {'login_form': login_form})

def username(email):
    user = registerUser.objects.get(email=email)
    return user.name, user.email


def reset_password(request):
    if request.POST.get('password') == request.POST.get('confirmnewpassword'):
        password = request.POST.get( 'password' )
        email = request.POST.get('email')
        changepassword = registerUser.objects.get(email=email)
        changepassword.password = make_password(password)
        changepassword.token_id = ''
        changepassword.save()
        return render (request,'reset_pass.html')
    else:
        messages.error(request,'Password and confirm password does not match')
 
@csrf_exempt
def forgot_password(request):
    if request.GET.get('token') is not None:
        email = request.GET.get('email')
        user, email = username(email)
        return render(request, 'password_link.html',{'user':user, 'email':email})
    
    if request.method == "POST":
        email =  request.POST.get('email')
        check_email = find_email(email)
        if check_email is True:
            token = secrets.token_hex(8)
            token_str = ''.join(token)
            store = store_token(token_str, email)
            email_str = ''.join(email)
            subject = 'Reset Password'
            message = f"We heard that you lost your Password. Sorry about that! But don’t worry! You can use the following link to reset your password: http://127.0.0.1:8000/home/user_login/forgot_password/?token={token_str}&email={email_str}"    
            from_email = 'khushiii41123@gmail.com'
            recipient_list = ['khushiii41123@gmail.com']
            send_mail(subject, message, from_email, recipient_list)
            
        return render(request, 'forgot_password_emailsuccess.html')
    else:
        print(request.GET)
    return render(request, 'forgot_password.html')

def store_token(token, emailid):
    user = registerUser.objects.get(email= emailid)
    print(len(token))
    user.token_id = token
    user.save()
    
    return user.id 
def find_email(email):
    try:
        user = registerUser.objects.get(email=email)
        return True
    except registerUser.DoesNotExist:
        return None

@csrf_exempt
def password_link(request):
    try:
        if request.method == "POST":
            email = request.POST.get('email')
            print(email)
            password = request.POST['password']
            repassword = request.POST['repassword']

            userinfo = registerUser.objects.filter(email=email)
            for user in userinfo:
                user.password = password
                user.confirmpassword = repassword
                user.token_id = ""
                user.save()

        return (request, 'password_link.html')
    except:
        return (request, 'password_link_unsuccessful.html')


def check_validate(email, passsword):
    try:
        user = registerUser.objects.get(email=email)
        passs = check_password(passsword, user.password)
        print(passs)
        if passs:
            return user.id, user.email, user.password
    except registerUser.DoesNotExist:
        pass
    return None, None, None

def user_name(id):
    user = registerUser.objects.get(id=id)

    return user.name


@csrf_exempt
@user_login_required
def update_password(request):
    return render(request, 'update_password.html')

def product_details(request):
    if request.GET.get('product_id') is not None:
        product_id = request.GET.get('product_id')
        quantity = 1
        products = Products.objects.get(id=product_id)
        brand= products.brand
        brandname = brand_name(brand)
        products.brand = brandname
        try:
            reviews = Review.objects.filter(productid = product_id)
            for review in reviews:
                userid = review.userid
                username = user_name(userid)
                review.userid = username
            return render(request, 'product_details.html', {'products': products, 'quantity': quantity,'reviews':reviews})
        except reviews.DoesNotExist:
            return render(request, 'product_details.html', {'products': products, 'quantity': quantity})
    else:
        if request.GET.get("productname") is not None or request.GET.get("image") is not None:
            productname = request.GET.get("productname")
            img = request.GET.get("image")
            products = Products.objects.get(Q(productname=productname) | Q(image__icontains=img))
            quantity = 1
            brand = products.brand
            brandname = brand_name(brand)
            products.brand = brandname
            try:
                product_id = find_product_id(productname)
                reviews = Review.objects.filter(productid = product_id)
                for review in reviews:
                    userid = review.userid
                    username = user_name(userid)
                    review.userid = username
                return render(request, 'product_details.html', {'products': products, 'quantity': quantity,'reviews':reviews})
            except Review.DoesNotExist:
                return render(request, 'product_details.html', {'products': products, 'quantity': quantity})
        else:
            return render(request, 'product_details_empty.html')

def find_product_id(product_name):
    product = Products.objects.get(Q(productname__icontains =  product_name))
    return product.id

@csrf_exempt
def savereview(request):
    print(request.POST)
    productid = request.POST.get('product_id')
    rating= request.POST.get('rating')
    review = request.POST.get('savereview')
    userid = usercheck(request)
    productname , img, price = product_name(productid)

    if Orders.objects.filter(products = productname, userid= userid):
        savingreview = Review()
        savingreview.userid = userid
        savingreview.productreview = review
        savingreview.star_rating = rating
        savingreview.productid = productid
        savingreview.save()
    else:
        print("Yo Chill Girl buy it first!")
        print("No Order No Review!")
        messages.error(request,'Need to buy this product before Adding a Review')
        
    return HttpResponseRedirect(reverse('product_details'))

def manageproduct(request):
    products = Products.objects.all()
    for product in products:
        product.brand = brand_name(product.brand)
    return render(request, 'manage_product.html', {'products': products})


def brand_name(brand):
    try:
        brand_obj = Brands.objects.get(id=brand)
        return brand_obj.brandname
    except:
        print("Brand does not exist!")


def updateproduct(request, id):
    product = Products.objects.get(id=id)
    template = loader.get_template('updateproduct.html')
    context = {'product': product, }
    return HttpResponse(template.render(context, request))


def updaterecord(request, id):
    if request.method == "POST":
        product = Products.objects.get(id=id)

        product.productname = request.POST['productname']
        product.quantity = request.POST['quantity']
        product.status = request.POST['status']
        brand = request.POST['brand']
        brand_id = get_brand(brand)
        product.brand = brand_id

        if 'image' in request.FILES:
            product.image = request.FILES['image']

        product.save()

        return HttpResponseRedirect(reverse('product'))


def deleteproduct(request, product_id):
    product = Products.objects.get(id=product_id)
    product_name = product.productname
    product.delete()
    return render(request, 'deleteproduct.html', {'product_name': product_name})


def add_product(request):

    product = None
    form = ProductForm(request.POST, request.FILES)
    if request.method == "POST":

        '''print(form.cleaned_data['imgfile'])
        exit()'''

        if form.is_valid():
            product = form.save(commit=False)
            product.productname = form.cleaned_data['productname']
            product.quantity = form.cleaned_data['quantity']
            product.status = form.cleaned_data['status']

            product.image = request.FILES['image']

            # getting the value of the brand name
            brand = form.cleaned_data['brand']
            # getting the brand name
            brand_id = get_brand(brand)

            product.brand = brand_id

            product.save()
            transaction.commit()
            return redirect('manage_product')
    else:
        form = ProductForm()

    return render(request, "products.html", {"form": form, 'product': product})


'''
def uploadImageView(request):
    form = ProductForm(request.POST or None, request.FILES or None)
    if request.method == "POST":
        if form.is_valid():
            form.save()
            Context['form'] = form
        request.session['image'] = request.POST['image']
        return redirect('image:create')'''


def get_brand(brand):
    try:
        brand_obj = Brands.objects.get(brandname=brand)
        return brand_obj.id
    except Brands.DoesNotExist:
        # If the brand does not exist create one brand
        new_brand = Brands(brandname=brand)
        new_brand.save()
        transaction.commit()
        return new_brand.id


def product_list(request):
    products = Products.objects.all()
    for product in products:
        product.brand = brand_name(product.brand)

    return render(request, 'product_list.html', {'products': products})


def success_page(request):
    return render(request, 'success_page.html')


def brand(request):
    form = BrandForm()
    if request.method == 'POST':
        form = BrandForm(request.POST)
        if form.is_valid():
            brand = form.save(commit=False)
            brand.brandname = form.cleaned_data['brandname']
            brand.save()
            transaction.commit()
            return redirect('brand_list')
    else:
        print(form.errors)

    return render(request, 'brand.html', {'form': form})


def brand_list(request):
    brands = Brands.objects.all()
    return render(request, 'brand_list.html', {'brands': brands})

@csrf_exempt
def user_profile(request):
    if 'email' in request.session and request.session['email'] != "":
        email = request.session['email']
        user = registerUser.objects.get(email=email)
        user_login_form = userProfile(instance=user)
        return render(request, 'user_profile.html', {'userLogin': user_login_form})
    else:
        print('email is blank')
        return redirect('user_login')

@csrf_exempt
def userUpdate(request):
    userid = usercheck(request)
    print(request.POST)
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        address = request.POST['address']
        phonenumber = request.POST['phonenumber']
        
        registerUser.objects.filter(id=userid).update(name= username, email= email, address= address, phone_number=phonenumber )
        
        return redirect('home')
    else:
        return redirect('user_profile')


def logout_view(request):
    request.session['email'] = None
    request.session['id'] = None
    logout(request)
    return redirect('user_login')
