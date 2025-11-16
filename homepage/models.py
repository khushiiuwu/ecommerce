from django.db import models
from django.conf import settings
from PIL import Image 
import os
from django.core.validators import RegexValidator, validate_comma_separated_integer_list

# Create your models here.


'''
def upload_location(instance, filename):
    filebase, extension = filename.split(".")
    return "%s%s.%s"('picx', uuid.uuid4(), extension)
  '''  

class registerUser(models.Model):
    name =  models.CharField(max_length=35)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)
    confirmpassword = models.CharField(max_length=128)
    address = models.CharField(max_length=128) 
    phone_number = models.CharField(max_length=10, validators=[RegexValidator(r'^\d{1,10}$')])
    token_id = models.CharField(max_length=16, default='0')
    
class Carts(models.Model):
    productdetails = models.CharField(validators=[validate_comma_separated_integer_list], max_length=120)
    userid = models.IntegerField(default=0)
    qty = models.CharField(max_length=4)
    
class Wishlist(models.Model):
    image = models.CharField(max_length=128)
    productname = models.CharField(max_length=40)
    userid = models.IntegerField()
    date = models.DateField(auto_now_add=True)
    

class Review(models.Model):
    userid = models.IntegerField()
    productreview = models.CharField(max_length=66)
    star_rating = models.IntegerField()
    productid = models.IntegerField()

class Products(models.Model):
    productname = models.CharField(max_length=40)
    productdescription = models.TextField(default=None)
    quantity = models.IntegerField()
    status = models.CharField(max_length=35)
    brand = models.CharField(max_length=35)
    image = models.ImageField(upload_to='products/image',default=None)
    image2 = models.ImageField(upload_to='products/image', default=None)
    image3 = models.ImageField(upload_to="products/image", default=None)
    price = models.IntegerField(default=0)
    Type = models.CharField(max_length=35,null=True)
    material = models.CharField(max_length=35, null=True)
    color = models.CharField(max_length=35, null=True)
    category = models.CharField(max_length=35)
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        # Define the destination directory within the static folder
        static_dir = os.path.join(settings.BASE_DIR, 'static', 'products', 'image')

        # Create the directory if it doesn't exist
        os.makedirs(static_dir, exist_ok=True)

        # Process each image field
        for image_field_name in ['image', 'image2', 'image3']:
            # Get the image field
            image_field = getattr(self, image_field_name)

            if image_field and image_field.name:
                # Get the file name
                file_name = os.path.basename(image_field.name)

                # Construct the destination file path
                destination_path = os.path.join(static_dir, file_name)

                # Open the image using PIL
                img = Image.open(image_field.path)

                # Resize if necessary
                if img.height > 300 or img.width > 300:
                    output_size = (300, 300)
                    img.thumbnail(output_size)
                    img.save(destination_path)

                # Update the image field to reflect the new location
                image_field.name = os.path.join('image', file_name).replace('\\', '/')

                # Remove the "static" part from the image URL stored in the database
                image_field.name = image_field.name.replace('static\\', '').replace('static/', '')

        # Save the changes to the model
        super().save(*args, **kwargs)
        

    """def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        # Define the destination directory within the static folder
        static_dir = os.path.join(settings.BASE_DIR, 'static', 'products', 'image')

        # Create the directory if it doesn't exist
        os.makedirs(static_dir, exist_ok=True)

        # Get the file name
        file_name = os.path.basename(self.image.name)

        # Construct the destination file path
        destination_path = os.path.join(static_dir, file_name)

        # Open the image using PIL
        img = Image.open(self.image.path)

        # Resize if necessary
        if img.height > 300 or img.width > 300:
            output_size = (300, 300)
            img.thumbnail(output_size)
            img.save(destination_path)

        # Update the image field to reflect the new location
        self.image.name = os.path.relpath(destination_path, settings.STATIC_ROOT)

        # Save the changes to the model
        super().save(*args, **kwargs)"""
    
    """ OLD FUNCTION def save(self): # new   
        super().save()
        img = Im.open(self.image.path)
        # resize it
        if img.height > 300 or img.width > 300:
            output_size = (300,300)
            img.thumbnail(output_size)
            print(self.image.path)
            img.save(self.image.path)"""
    
class Category(models.Model):
    category = models.CharField(max_length=35)

           
class Brands(models.Model):
    brandname = models.CharField(max_length=25)

class Coupons(models.Model):
    couponname = models.CharField(max_length=5)
    type = models.CharField(max_length=10)
    amount = models.IntegerField()
    restriction = models.IntegerField()
    used_count = models.IntegerField()
    
class Address(models.Model):
    billing_address = models.CharField(max_length=255)
    billing_city = models.CharField(max_length=35)
    billing_postcode = models.IntegerField()
    billing_phonenumber = models.CharField(max_length=10, validators=[RegexValidator(r'^\d{1,10}$')] )
    billing_email = models.EmailField(unique=True)
    shipping_address = models.CharField(max_length=255)
    shipping_city = models.CharField(max_length=35)
    shipping_postcode = models.IntegerField()
    shipping_phonenumber = models.CharField(max_length=10, validators=[RegexValidator(r'^\d{1,10}$')] )
    shipping_email = models.EmailField(unique=True)
    user_id = models.IntegerField()
    
class Orders(models.Model):
    orderid = models.CharField(max_length=255)
    shipping = models.CharField(max_length=255)
    billing = models.CharField(max_length=255)
    total = models.IntegerField()
    products = models.CharField(max_length=40)
    quantity = models.IntegerField()
    status = models.CharField(max_length=25)
    payment_mode = models.CharField(max_length=35)
    discount = models.IntegerField()
    couponcode = models.CharField(max_length=5)
    transaction_id = models.CharField(max_length=10)
    userid = models.IntegerField()
    date = models.DateField(auto_now_add=True)