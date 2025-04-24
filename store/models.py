from typing import Any
from django.db import models
import datetime
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator

# Create your models here.

class Catogery(models.Model):
    name=models.CharField(max_length=30)
    
    def __str__(self):
        return self.name
    
    class Meta:
       verbose_name_plural = 'categories'



class Customer(models.Model):
    first_name=models.CharField(max_length=30)
    last_name=models.CharField(max_length=30)
    phone =models.CharField(max_length=10)
    email =models.EmailField(max_length=100)
    password =models.CharField(max_length=20)

    def __str__(self):  
        return f'{self.first_name} + {self.last_name}'



class Product(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True,null=True)
    catogery = models.ForeignKey(Catogery, on_delete=models.CASCADE, null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to="uploads/products/",null=True,blank=True)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    review_count = models.PositiveIntegerField(default=0)
    embedding = models.JSONField(null=True, blank=True)  # Stores LLM-generated vector
    is_sale = models.BooleanField(default=False)
    sale_price = models.DecimalField(default=0, decimal_places=2, max_digits=6)

    def __str__(self):
        return self.name
    def save(self, *args, **kwargs):
        if not self.embedding and self.description:
            try:
                from sentence_transformers import SentenceTransformer
                model = SentenceTransformer('all-MiniLM-L6-v2')
                self.embedding = model.encode(self.description[:512]).tolist()  # Truncate to 512 tokens
            except Exception as e:
                print(f"Embedding generation failed: {e}")
            # Consider queueing this for async processing
        super().save(*args, **kwargs)

class Order(models.Model):
    product=models.ForeignKey(Product,on_delete=models.CASCADE)
    customer=models.ForeignKey(Customer,on_delete=models.CASCADE)
    quantity=models.IntegerField(default=1)
    address=models.CharField(max_length=50,default='',blank=True)
    phone =models.CharField(max_length=20,default='',blank=True)
    date =models.DateField(default=datetime.datetime.today)
    status=models.BooleanField(default=False)

    def __str__(self):
       return f"{self.product} {self.quantity}"
    

class RecommendationLog(models.Model):
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    source_product = models.ForeignKey(Product, null=True, on_delete=models.SET_NULL)
    recommended_products = models.ManyToManyField(Product, related_name='recommendation_logs')
    timestamp = models.DateTimeField(auto_now_add=True)
    clicked = models.BooleanField(default=False)


class ProductReview(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating from 1 to 5"
    )
    review = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('product', 'user')  # One review per user per product
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.rating} stars by {self.user.username} for {self.product.name}"


class ProductVisit(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    visited_at = models.DateTimeField(auto_now=True)

    # Removed the unique_together constraint
    class Meta:
        ordering = ['-visited_at']  