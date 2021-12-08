from django.contrib import admin

from app.models import Order, Category

admin.site.register(Category)
admin.site.register(Order)
