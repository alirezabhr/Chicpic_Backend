from django.urls import path

from . import views


urlpatterns = [
    path('categories/', views.CategoriesView.as_view(), name='categories'),
    path('categories/<int:category_id>/products/', views.CategoryProductsView.as_view(), name='category_products'),
    path('categories/<int:category_id>/variants/', views.CategoryVariantsView.as_view(), name='category_variants'),
    path('categories/discounted/variants/', views.DiscountedCategoryVariantsView.as_view(), name='discounted_category'),
    path('shops/', views.ShopsView.as_view(), name='shops'),
    path('shops/<int:shop_id>/products/', views.ShopProductsView.as_view(), name='shop_products'),
    path('shops/<int:shop_id>/variants/', views.ShopVariantsView.as_view(), name='shop_variants'),
    path('explore/variants/', views.ExploreVariantsView.as_view(), name='explore_variants'),
    path('products/', views.ProductsView.as_view(), name='products'),
    path('products/<int:product_id>/', views.ProductDetailView.as_view(), name='product_detail'),
    path('search/', views.VariantSearchView.as_view(), name='search_variants'),
    path('save/', views.SaveVariantView.as_view(), name='save_variant'),
    path('track/', views.TrackVariantView.as_view(), name='track_variant'),
    path('saved/<int:user_id>/', views.SavedVariantsView.as_view(), name='saved_variants'),
]
