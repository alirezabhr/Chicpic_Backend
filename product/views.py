from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny

from .models import Category
from .serializers import CategorySerializer


class CategoriesView(ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = CategorySerializer

    def get_queryset(self):
        gender = self.request.query_params.get('gender')
        if gender is not None:
            return Category.objects.filter(gender=self.request.query_params.get('gender'))
        return Category.objects.all()
