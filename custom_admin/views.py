from django.shortcuts import get_object_or_404, render, redirect
from django.core.files.storage import default_storage
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.hashers import check_password
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.template import loader
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from PIL import Image 
from .decorators import admin_login_required
from .forms import UserForm
from .models import Users
from homepage.models import Products, Brands, Orders, Address, Review, registerUser, Category
from homepage.forms import ProductForm, OrdersForm
import json,os
import urllib

#ADMIN LOGIN VIEW
def login_view(request):
    if 'email' in request.session and request.session['email'] != "":
        print(request.session['email'])

        return redirect('admin_panel')
    
    admin_login = UserForm()
    
    if request.method =='POST':
        res_data = request.POST
        
        password1 = res_data.get("password")
        email1 = res_data.get("email")
    
        print(password1)
        user_id, email = check_validate(email1, password1)
        print(check_validate(email1, password1))
        # print(user_id)
        if user_id is not None:
                add_session(request, email, user_id)
                return redirect('admin_panel')
        
        else:
            print("having error here")
            messages.error(request,' Invalid username or password is incorrect')
            return redirect('login')
    else:
        admin_login = UserForm()
            
    return render(request, 'admin_login.html', {'admin_login':admin_login })
  
#ADMIN DASHBOARD  
@admin_login_required
def admin_panel(request):
    customercount = registerUser.objects.all().count()
    productcount = Products.objects.all().count()
    ordercount = Orders.objects.all().count()
    
    orders= Orders.objects.order_by('-id')[:5]
    ordered_products=[]
    ordered_bys=[]
    for order in orders:
        ordered_product= Products.objects.all().filter(productname = order.products)
        ordered_by= registerUser.objects.all().filter(id = order.userid)
        ordered_products.append(ordered_product)
        ordered_bys.append(ordered_by)
        
    mydict = {
        'customercount':customercount,
        'productcount': productcount,
        'ordercount' : ordercount,
        'data': zip(ordered_products, ordered_bys, orders)
    } 
    return render(request, 'admin.html', context=mydict)
#AMIN PROFILE 
@admin_login_required
def admin_profile(request):
    userid = usercheck(request)
    print(userid)

    users = Users.objects.filter(id=userid)
    return render(request, 'admin_profile.html',{'users':users})

#UPDATE PROFILE
@admin_login_required
@csrf_exempt
def update_profile(request):
    user_id = usercheck(request)
    
    password = request.POST.get('password')
    newpassword = request.POST.get('newpassword')
    
    user = Users.objects.get(id=user_id)    
    originalpassword = user.password
    
    if password == originalpassword:
        user.password = newpassword
        user.save()
    else:
        print("Please enter correct existing password!")
        return redirect('admin_profile') 
        
    return redirect('admin_panel')

#------PRODUCT MANAGEMENT------

#ADD PRODUCTS
@csrf_exempt
@admin_login_required
def add_product(request):
    category = Category.objects.all()
    product = None
    if request.method == "POST":
        print(request.POST)
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.productname = form.cleaned_data['productname']
            product.quantity = form.cleaned_data['quantity']
            product.status = form.cleaned_data['status']
            #product.image = request.FILES['img']
            product.productdescription = form.cleaned_data['productdescription']
            categoryname = request.POST['category']
            categoryid =  category_name(categoryname)
            
            product.category = categoryid

            if 'img[]' in request.FILES:
                images = request.FILES.getlist('img[]')
                for image in images:
                    # Process each image here
                    pass
                
            #getting the value of the brand name
            brand = form.cleaned_data['brand']
            #getting the brand name
            brand_id = get_brand(brand)
            product.brand = brand_id
            product.save()
     
            messages.success(request, "Product Added Successfully!" )

            return HttpResponseRedirect(reverse('add_product'))
        else:
            print(form.errors)
    
    return render(request, 'add_product.html',{'category':category})

#FINDING CATEGORY NAME
def category_name(categoryname):
    try:
        category = Category.objects.get(Q(category__icontains=categoryname))
        return category.id
    except Category.DoesNotExist:
        new_category = Category(category=categoryname)  
        new_category.save()
        return new_category.id
        

#FINDING BRAND NAME
def get_brand(brand):
    try:
        brand_obj = Brands.objects.get(brandname=brand)
        return brand_obj.id
    except Brands.DoesNotExist:
        #If the brand does not exist create one brand
        new_brand = Brands(brandname=brand) 
        new_brand.save()
        return new_brand.id   
#BRAND NAME
def brand_name(brand):
   try:
       brand_obj = Brands.objects.get(id=brand)
       return brand_obj.brandname
   except:
       print("Brand does not exist!")
       



#UPDATE PRODUCT DETAILS
@csrf_exempt
@admin_login_required
def update_productdetails(request):
    product = Products.objects.all()
    p = Paginator(product, 5)    
    page_number = request.GET.get('page')
    
    try:
        page_obj = p.get_page(page_number)
    except PageNotAnInteger:
        page_obj = p.page(1)
    except EmptyPage:
        page_obj = p.page(p.num_pages)
            
    page_range1 = p.page_range
    return render(request, "update_productdescription.html",{'products':page_obj,'page_obj':page_obj, 'page_iterate':page_range1})

@csrf_exempt
@admin_login_required
def product_description(request,id):
    product = Products.objects.get(id=id)
    template = loader.get_template('product_description.html')
    context = {'product':product,}
    return HttpResponse(template.render(context, request))

@csrf_exempt
@admin_login_required
def details(request,id):
        if request.method == "POST":
            print(request.POST)
            #PRODUCT DETAILS
            productname = request.POST.get('productname')
            quantity = request.POST.get('quantity')
            status = request.POST.get('status')
            brand= "voguevault"
            brand_id = get_brand(brand)
            price = request.POST.get('price')
            product_description = request.POST.get('productdescription')
            tYpe = request.POST.get('type')
            color = request.POST.get('color')
            material = request.POST.get('material')
            categoryname = request.POST.get('category')
            category = category_find(categoryname)

            if not bool(request.FILES):
                print(request.POST)
                Products.objects.filter(id=id).update(productname= productname, quantity= quantity, status=status, brand = brand_id,price=price,Type=tYpe,color= color, productdescription=product_description, material= material, category= category)
                print("Updated Description")
            else:
                image = request.FILES.get('image')
                image2 = request.FILES.get('image2')
                image3 = request.FILES.get('image3')

                # Define the destination directory within the static folder
                static_dir = os.path.join(settings.BASE_DIR, 'static', 'products', 'image')
                

                # Save each image to the destination directory
                if image:
                    with open(os.path.join(static_dir, image.name), 'wb') as destination:
                        for chunk in image.chunks():
                            print(chunk)
                            destination.write(chunk)

                if image2:
                    with open(os.path.join(static_dir, image2.name), 'wb') as destination:
                        for chunk in image2.chunks():
                            destination.write(chunk)

                if image3:
                    with open(os.path.join(static_dir, image3.name), 'wb') as destination:
                        for chunk in image3.chunks():
                            destination.write(chunk)

                # Update product description
                
                
                # Prepare the update data for the database
                update_data = {'productname':productname,'quantity':quantity,'status':status,'brand':brand_id , 'price':price,'Type':tYpe,'material':material, 'color':color,'productdescription': product_description,'category':category}

                # Check if images exist and update the corresponding fields
                if image:
                    update_data['image'] = 'image/' + image.name
                if image2:
                    update_data['image2'] = 'image/' + image2.name
                if image3:
                    update_data['image3'] = 'image/' + image3.name

                # Update the database with image paths and description
                Products.objects.filter(id=id).update(**update_data)
                print("updated all fields")

                """image1 = 'image/'+ str(request.FILES.get('image'))
                image2 = 'image/'+ str(request.FILES.get('image2'))
                image3 = 'image/'+ str(request.FILES.get('image3'))
                product_description = request.POST.get('productdescription')
                Products.objects.filter(id=id).update(image= image1, image2=image2, image3=image3, productdescription=product_description)"""
                print("updated all fields")
                
        return HttpResponseRedirect(reverse('update_productdetails'))

def category_find(categoryname):
    catname = categoryname.isnumeric()
    if catname is True:
        try:
            category = Category.objects.get(id = categoryname)
            return category.id
        except Category.DoesNotExist:
            return None
    else:
        try:
            category = Category.objects.get(Q(category__icontains=categoryname))
            return category.id
        except Category.DoesNotExist:
            new_category = Category(category=categoryname)  
            new_category.save()
            return new_category.id
   
#UPDATE PRODUCTS
@csrf_exempt
@admin_login_required
def update_product(request): 
    products = Products.objects.all()
    for product in products:
        bb = brand_name(product.brand)
        product.brand = brand_name(product.brand)
    
    p = Paginator(products, 4)    
    page_number = request.GET.get('page')
    
    try:
        page_obj = p.get_page(page_number)
    except PageNotAnInteger:
        page_obj = p.page(1)
    except EmptyPage:
        page_obj = p.page(p.num_pages)
            
    page_range1 = p.page_range
    
    print("TYPE OF PAGE ITERATE", type(page_obj))
    return render(request, 'update_product.html', {'products': page_obj,'page_obj':page_obj, 'page_iterate':page_range1} )

#DETAILS OF PRODUCT
@admin_login_required
def product(request, id):
    product = Products.objects.get(id=id)
    template = loader.get_template('product_details_update.html')
    context = {'product':product,}
    return HttpResponse(template.render(context, request))

#ACTUALLY UPDATING THE PRODUCT
@csrf_exempt
@admin_login_required
def update_record(request, id):
    product = Products.objects.get(id=id)
    
    if request.method == "POST":
        product.productname = request.POST['productname']
        product.quantity = request.POST['quantity']
        product.status = request.POST['status']
        brand = request.POST['brand']
        brand_id = get_brand(brand)
        product.brand = brand_id
        product.price = request.POST['price']
        image = request.FILES.get('image')

        if image:
            destination_dir = os.path.join(settings.BASE_DIR, 'static', 'products', 'image')
            # Ensure the destination directory exists
            os.makedirs(destination_dir, exist_ok=True)
            # Construct the destination path for the image file
            destination_path = os.path.join(destination_dir, image.name)
            # Save the image file to the destination path
            with open(destination_path, 'wb') as destination:
                for chunk in image.chunks():
                    destination.write(chunk)
            # Update the product's image field
            product.image = 'image/' + image.name
           
        
        product.save()
        print("Updated Successfully!")
        
        messages.success(request, "Product Updated Successfully!" )

        # Redirect to the product list view after updating
        return HttpResponseRedirect(reverse('update_product'))

    return render(request, 'product_details_update.html', {'product': product})

@csrf_exempt   
@admin_login_required
def delete_product(request, product_id):
    product = get_object_or_404(Products, id=product_id)
    product.delete()
    messages.success(request, "Product Deleted Successfully!" )
    messages.error(request, "Product Not Deleted!" )
    # Redirect to the product list view after deletion
    return HttpResponseRedirect(reverse('update_productdetails'))

#------PRODUCT MANAGEMENT ENDS------

#------CATEGORY MANAGEMENT------
@csrf_exempt
@admin_login_required
def category(request):
    return render(request, 'add_category.html')

@csrf_exempt
@admin_login_required
def add_category(request):
    categoryname = request.POST.get('category')
    Category(category=categoryname).save() 
    messages.success(request ,"Added New Category",categoryname,"Successfully!")
    return HttpResponseRedirect(reverse('category'))



@csrf_exempt
def update_category(request):
    category = Category.objects.all()
    return render(request, "update_category.html",{'category':category})

#------CATEGORY MANAGEMENT ENDS------

#------ORDER MANAGEMENT------

#MANAGING ORDERS
@admin_login_required
def manage_orders(request):
    if request.GET.get('sortby'):
        status = request.GET.get('sortby')
        if status == "All Orders":
            orders = Orders.objects.all()
            p = Paginator(orders, 10)    
            page_number = request.GET.get('page')
            
            try:
                page_obj = p.get_page(page_number)
            except PageNotAnInteger:
                page_obj = p.page(1)
            except EmptyPage:
                page_obj = p.page(p.num_pages)
                    
            page_range1 = p.page_range

            return render(request, 'manage_orders.html', {'orders':page_obj,'page_obj':page_obj, 'page_iterate':page_range1})
        print("ORDER STATUS",status)
        orders = Orders.objects.filter(status=status)
        p = Paginator(orders, 10)    
        page_number = request.GET.get('page')
        
        try:
            page_obj = p.get_page(page_number)
        except PageNotAnInteger:
            page_obj = p.page(1)
        except EmptyPage:
            page_obj = p.page(p.num_pages)
                
        page_range1 = p.page_range

        return render(request, 'manage_orders.html', {'orders':page_obj,'page_obj':page_obj, 'page_iterate':page_range1})
    else:
        orders = Orders.objects.all()
        p = Paginator(orders, 10)    
        page_number = request.GET.get('page')
        
        try:
            page_obj = p.get_page(page_number)
        except PageNotAnInteger:
            page_obj = p.page(1)
        except EmptyPage:
            page_obj = p.page(p.num_pages)
                
        page_range1 = p.page_range

        return render(request, 'manage_orders.html', {'orders':page_obj,'page_obj':page_obj, 'page_iterate':page_range1})

#-------ORDERS---PENDING-----------

@csrf_exempt
@admin_login_required
def edit_order(request, id):
    order = Orders.objects.get(id=id)
    print(order)
    if request.method == "POST":
        print(order.products)
        order.status = request.POST.get('status')
        order.save()
        print("Updated Successfully!")
        messages.success(request, "Order Updated Successfully!")

        # Redirect to the product list view after updating
        return HttpResponseRedirect(reverse('manage_orders'))

    return render(request, 'manage_order_details.html', {'orders': order})

#EDITING AN ORDER
@csrf_exempt
@admin_login_required
def order_stats(request, id):
    order = Orders.objects.get(id=id)
    template = loader.get_template('manage_order_details.html')
    context = {'orders':order,}
    return HttpResponse(template.render(context, request))

#Deleting an order
@csrf_exempt
@admin_login_required
def delete_order(request, id):
    order = get_object_or_404(Orders, id=id)
    order.delete()

    # Redirect to the product list view after deletion
    return HttpResponseRedirect(reverse('manage_orders'))
#-------ORDERS PENDING ENDS-------


#-------ADD--ORDERS--------
@csrf_exempt
@admin_login_required
def add_orders(request):
    users = registerUser.objects.all()
    products = Products.objects.all()
    return render(request,'add_orders.html', {'users':users, 'products':products})

def user_order(request, productId):
    products = Products.objects.get(id = productId)
    
    product = {}
    product['productname'] = products.productname
    product['price'] = products.price
    product['id'] = productId
    product['quantity'] = products.quantity
    
    print(product)
    
    return JsonResponse({'product':product})

@csrf_exempt
@admin_login_required
def place_order(request):

    userid = request.POST.get('userid')
    prodDetails = request.POST.dict()
    
    product_id = [int(key.split('[')[1][:-1]) for key in prodDetails.keys() if '[' in key and key.startswith('prodDetails')]
    prod_quantity = [prodDetails[key] for key in prodDetails.keys() if '[' in key and key.startswith('prodDetails')]
    print(product_id, prod_quantity)
    print(userid)
    print( prodDetails)
    
    
 
    address = Address.objects.get(user_id = userid)
    for prod, qty in zip(product_id,prod_quantity):
            prodname = Products.objects.get(id=prod)
            print(prodname)
            order = Orders.objects.create(
                    shipping=address.id,
                    billing=address.id,
                    products=prodname.productname,
                    total= int(qty) * int(prodname.price),
                    quantity=qty,
                    status="Order Confirmed",
                    payment_mode="COD",
                    discount=0,
                    couponcode='',
                    transaction_id='',
                    userid=userid,
                    orderid=''
                    )
            order.save()
        
        
    
    
    messages.success(request, "Order Successful!")
    
    return HttpResponseRedirect(reverse('add_orders'))
    
#-------ADD ORDERS ENDS--------

#------ORDER MANAGEMENT ENDS-----------

#------USER--MANAGEMENT------

@csrf_exempt
@admin_login_required
def manage_feedback(request):
    reviews = Review.objects.all()
    for review in reviews:
        productname = find_product_name(review.productid)
        user_name = find_user_name(review.userid)
        review.productid = productname
        review.userid = user_name
    p = Paginator(reviews, 5)    
    page_number = request.GET.get('page')
    
    try:
        page_obj = p.get_page(page_number)
    except PageNotAnInteger:
        page_obj = p.page(1)
    except EmptyPage:
        page_obj = p.page(p.num_pages)
            
    page_range1 = p.page_range
    
    return render(request, 'manage_feedback.html',{'reviews':page_obj,'page_obj':page_obj, 'page_iterate':page_range1})

@csrf_exempt
@admin_login_required
def delete_review(request, id):
    print(id)
    review = Review.objects.get(id=id)
    review.delete()
    return HttpResponseRedirect(reverse('manage_feedback'))
    

def find_product_name(productid):
    product = Products.objects.get(id=productid)
    return product.productname

def find_user_name(userid):
    user = registerUser.objects.get(id=userid)
    return user.name
#------USER--MANAGEMENT ENDS-----

#------USER--MANAGEMENT------
@csrf_exempt
@admin_login_required
def manage_users(request):
    users = registerUser.objects.all()
    return render(request, 'manage_users.html', {'users':users})

#------EDIT--USER------
@csrf_exempt
@admin_login_required
def edit_user(request, id):
    users = registerUser.objects.get(id=id)
    template = loader.get_template('user_details.html')
    context = {'users':users,}
    return HttpResponse(template.render(context, request))

@csrf_exempt
@admin_login_required
def user(request, id):
    user = registerUser.objects.get(id=id)
    print(user)
    if request.method == "POST":
        user.name = request.POST.get('name')
        user.email = request.POST.get('email')
        user.address = request.POST.get('address')
        user.phone_number = request.POST.get('phone_number')
        user.save()
        print("User Updated Successfully!")
        messages.success(request, "User Updated Successfully!")

        # Redirect to the product list view after updating
        return HttpResponseRedirect(reverse('manage_users'))

    return render(request, 'user_details.html', {'users': user})

#------EDIT USER ENDS------


#------DELETE--USER------
@csrf_exempt
@admin_login_required
def delete_user(request, id):
    user = get_object_or_404(registerUser, id=id)
    user.delete()

    # Redirect to the product list view after deletion
    return HttpResponseRedirect(reverse('manage_users'))
#------DELETE USER ENDS------

#------USER--ADDRESS---------
@csrf_exempt
@admin_login_required
def user_address(request, userId):
    if request.method == 'GET':
        print(request.method)
        address = Address.objects.get(user_id = userId)
        
        billing_address = f"{address.billing_address},  {address.billing_city},  {address.billing_postcode}, {address.billing_phonenumber},  {address.billing_email}"
        shipping_address = f"{address.shipping_address}, {address.shipping_city}, {address.shipping_postcode}, {address.shipping_phonenumber}, {address.shipping_email}"
        
        context = {}
        context['billing_address'] = billing_address
        context['shipping_address'] = shipping_address
        
        return JsonResponse({'context':context})
    else:
        print("It's not working T_T")
        return HttpResponse('Error')
#------USER ADDRESS ENDS---------

#------USER MANAGEMENT ENDS------


def check_validate(email, passsword):
    try:
       
        user = Users.objects.get(email=email)
        
        if  passsword ==  user.password :
            print("In here check validate!",user.password, user.id)
            return user.id, user.email
    except Users.DoesNotExist:
        pass
    return None, None

def add_session(request, email, user_id):
    request.session['email'] = email
    request.session['id'] = user_id
    return email, user_id

def usercheck(request):
    email = request.session['email'] 
    user = Users.objects.get(email=email)
    user_id = user.id
    return user_id

def admin_logout(request):
    request.session['email'] = None
    request.session['id'] = None
    logout(request)
    return redirect('login')