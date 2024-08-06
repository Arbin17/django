from django.contrib import admin
from . models import Catogery,Customer,Product,Order
# Register your models here.
admin.site.register(Catogery)
admin.site.register(Customer)
admin.site.register(Order)
admin.site.register(Product)