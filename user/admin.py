from django.contrib import admin
from user.models import User, UserAdditional, ShirtFit, TrouserFit

# Register your models here.
admin.site.register(User)
admin.site.register(UserAdditional)
admin.site.register(ShirtFit)
admin.site.register(TrouserFit)
