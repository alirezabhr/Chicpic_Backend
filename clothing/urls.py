from django.urls import path

from . import views


urlpatterns = [
    path('categories/', views.CategoriesView.as_view(), name='categories'),
    path('categories/<int:category_id>/products/', views.CategoryProductsView.as_view(), name='category_products'),
    path('shops/', views.ShopsView.as_view(), name='shops'),
    path('shops/<int:shop_id>/products/', views.ShopProductsView.as_view(), name='shop_products'),
    path('products/', views.ProductView.as_view(), name='products'),
    path('products/<int:product_id>/', views.ProductDetailView.as_view(), name='product_detail'),
    path('products/search/', views.ProductSearch.as_view(), name='products_search'),
]
