from django.urls import path

from . import views


urlpatterns = [
    path('categories/', views.CategoriesView.as_view(), name='get_categories'),
    path('categories/<int:category_id>/', views.CategoryProductsView.as_view(), name='category_products'),
    path('<int:product_id>/', views.ProductDetailView.as_view(), name='product_detail'),
]
