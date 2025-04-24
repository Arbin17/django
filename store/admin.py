from django.contrib import admin
from . models import Catogery,Customer,Product,Order,RecommendationLog, ProductReview
# Register your models here.
admin.site.register(Catogery)
admin.site.register(Customer)
admin.site.register(Order)
admin.site.register(Product)
admin.site.register(RecommendationLog)
admin.site.register(ProductReview)