from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views



urlpatterns =  [
    path("", views.home, name="home"),
    path("user_login/", views.login_view, name="user_login"),
    path("user_login/forgot_password/", views.forgot_password, name="forgot_password"),
    path("user_login/forgot_password/done/", views.password_link, name="password_link"),
    path("update_password/", views.update_password, name="update_password"),
    path("reset_password/", views.reset_password, name="reset_password"),
    path("user_profile/", views.user_profile, name="user_profile"),
    path("user_profile/userUpdate/", views.userUpdate, name="userUpdate"),
    path("cart/", views.add_cart, name="cart"),
    path("wishlist/", views.wishlist, name="wishlist"),
    path('remove_wishlist/', views.remove_wishlist, name="remove_wishlist"),
    path("remove_cart/<int:prod_id>", views.remove_cart, name="remove_cart"),
    path("add_qty/<int:prod_id>", views.add_qty, name="add_qty"),
    path("remove_qty/<int:prod_id>", views.remove_qty, name="remove_qty"),
    path("cart/checkout/", views.checkout, name="checkout"),
    path("cart/checkout/thankyou/", views.thankyou, name="thankyou"),
    path("cart/savecart/", views.savecart, name="savecart"),
    path("cart/coupon/", views.coupon, name="coupon"),
    path('my_order/', views.my_order, name="my_order"),
    path('trackorder/', views.trackorder, name="trackorder"),
    path('thankyou/', views.thankyou, name="thankyou"),
    path('shop/', views.shop, name='shop'),
    path('shop/product_details/', views.product_details, name="product_details"),
    path('savereview/',views.savereview, name="savereview"),
    path('about_us/', views.about_us, name='about_us'),
    path("contact_us/", views.contact_us, name="contact_us" ),
    path("savecontactus/", views.savecontactus, name="savecontactus" ),
    path("logout/", views.logout_view, name="logout"),

    path("main/", views.homepage , name="homepage"),
    path("paymenthandler/", views.paymenthandler, name="paymenthandler"),
    path("main/orderhistory/", views.orderhistory, name="orderhistory"),
    path("main/orderhistory/order/", views.order, name="order"),
    path("register/", views.Registeration, name="register"),
    path("product_list/", views.product_list, name="product_list"),
    path("product_list/add_cart/<int:id>", views.add_cart, name="add_cart"),
    path("manageproduct/", views.manageproduct, name="manageproduct"),
    path("manageproduct/updateproduct/<int:id>", views.updateproduct, name="updateproduct"),
    path("manageproduct/updateproduct/updaterecord/<int:id>", views.updaterecord, name="updaterecord"),
    path("manageproduct/deleteproduct/<int:product_id>", views.deleteproduct, name="deleteproduct"),
    path("success_page/", views.success_page, name="success" ),
    path("brand/", views.brand, name="brand"),
    path("brand_list/", views.brand_list,name="brand_list" ),
    ]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)