from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views



urlpatterns =  [
    path("", views.login_view, name="login"),
    path("admin_panel/", views.admin_panel, name="admin_panel"),
    path("admin_profile/", views.admin_profile, name="admin_profile"),
    path("update_profile/", views.update_profile, name="update_profile"),
    path("add_product/", views.add_product, name="add_product"),
    path("update_product/", views.update_product, name="update_product"),
    path("update_product/product/<int:id>", views.product, name="product"),
    path("update_product/product/update_record/<int:id>", views.update_record, name="update_record"),
    path("delete_product/<int:product_id>", views.delete_product, name="delete_product"),
    path("update_productdetails/", views.update_productdetails, name="update_productdetails"),
    path("update_productdetails/product_description/<int:id>", views.product_description, name="product_description"),
    path("details/<int:id>", views.details, name="details"),
    path("manage_orders/", views.manage_orders, name="manage_orders"),
    path("manage_orders/edit_order/<int:id>", views.edit_order, name="edit_order"),
    path("manage_orders/edit_order/order_stats/<int:id>", views.order_stats, name="order_stats"),
    path("manage_orders/delete_order/<int:id>", views.delete_order, name="delete_order"),
    path('manage_feedback/', views.manage_feedback, name="manage_feedback"),
    path('manage_feedback/delete_review/<int:id>', views.delete_review, name="delete_review"),
    path('category/', views.category, name="category"),
    path('add_category/', views.add_category, name="add_category"),
    path('update_category/', views.update_category, name="update_category"),
    path("add_orders/", views.add_orders, name="add_orders"),
    path("add_orders/place_order/", views.place_order, name="place_order"),
    path("user_address/<int:userId>", views.user_address, name="user_address"),
    path("user_order/<int:productId>", views.user_order, name="user_order"),
    path("manage_users/", views.manage_users, name="manage_users"),
    path("manage_users/edit_user/<int:id>", views.edit_user, name="edit_user"),
    path("manage_users/edit_user/user/<int:id>", views.user, name="user"),
    path("manage_users/delete_user/<int:id>", views.delete_user, name="delete_user"),
    path("admin_logout/",views.admin_logout, name="admin_logout" ),
    ]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
