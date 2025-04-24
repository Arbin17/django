from datetime import timedelta
import random  
from django.utils import timezone  
from django.shortcuts import render,redirect ,get_object_or_404
from .models import Catogery, Product, ProductReview, ProductVisit ,  RecommendationLog
from django.contrib.auth import login,logout,authenticate
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .forms import ReviewForm, SignUpForm
from django import forms
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
import requests
from django.db.models import Avg 
from django.views.decorators.http import require_GET

from store import models
FASTAPI_URL = "http://127.0.0.1:8000"
# Create your views here.

def home(request):
    products = list(Product.objects.all())
    random.shuffle(products)
    visited_ids = []
    
    if request.user.is_authenticated:
        # Get all unique product IDs visited in last 24 hours
        visits = ProductVisit.objects.filter(
            user=request.user,
            visited_at__gte=timezone.now() - timedelta(hours=1)
        ).values('product_id').distinct()
        
        visited_ids = [v['product_id'] for v in visits]
    
    return render(request, 'product/index.html', {
        'products': products,
        'visited_ids': visited_ids
    })

def catogery(request, ak):
    try:
        catogery = Catogery.objects.get(name=ak)
        products = Product.objects.filter(category=catogery)
        context = {"products": products, "category": catogery}
        return render(request, "product/category.html", context)
    except:  # noqa: E722
        messages.success(request, "That category does not exist, try again.")
        return redirect("product/index.html")


def product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    reviews = product.reviews.all().order_by('-created_at')
   
    if request.user.is_authenticated:
        ProductVisit.objects.update_or_create(
            user=request.user,
            product=product,
            defaults={'visited_at': timezone.now()}  # This will update the timestamp if record exists
        )
    # Calculate average rating
    reviews = product.reviews.all()
    rating_data = reviews.aggregate(average_rating=Avg('rating'))
    product.average_rating = rating_data['average_rating'] or 0
    product.review_count = reviews.count()
    
    # Review form handling
    review_form = None
    user_review = None
    
    if request.user.is_authenticated:
        try:
            user_review = ProductReview.objects.get(product=product, user=request.user)
        except ProductReview.DoesNotExist:
            user_review = None
        
        if request.method == 'POST':
            review_form = ReviewForm(request.POST, instance=user_review)
            if review_form.is_valid():
                review = review_form.save(commit=False)
                review.product = product
                review.user = request.user
                review.save()
                messages.success(request, "Thank you for your review!")
                return redirect('product', pk=pk)
        else:
            review_form = ReviewForm(instance=user_review)
    recommended_products = []
    
    try:
        if product.embedding:
            other_products = list(Product.objects.exclude(id=pk).filter(embedding__isnull=False))
            
            if other_products:
                embeddings = [p.embedding for p in other_products]
                
                try:
                    response = requests.post(
                    f"{FASTAPI_URL}/recommend",
                    json={
                     "target_embedding": product.embedding,
                    "all_embeddings": embeddings,
                    "user_data": {
                    "user_id": request.user.id if request.user.is_authenticated else None,
                    "product_id": product.id
                         }
                 },
                     timeout=5
                    )
                    response.raise_for_status()
                    print("RESPONSE JSON:", response.json())  # DEBUG HERE
                except requests.RequestException as e:
                    print("ERROR CALLING FASTAPI:", e)

                recommended_ids = response.json().get("recommended_ids", [])
                recommended_products = [other_products[i] for i in recommended_ids if i < len(other_products)]
                
                # Log recommendations
                if request.user.is_authenticated and recommended_products:
                    log = RecommendationLog.objects.create(
                        user=request.user,
                        source_product=product
                    )
                    log.recommended_products.set(recommended_products[:3])  # Log top 3
                    
    except requests.RequestException as e:
        # Fallback to simple recommendations if API fails
        recommended_products = Product.objects.filter(
            catogery=product.catogery
        ).exclude(id=pk).order_by('?')[:3]  # Random fallback
    
    return render(request, 'product/product.html', {
        'product': product,
        'reviews': reviews,
        'review_form': review_form,
        'user_review': user_review,
        'recommended_products': recommended_products,
    })

def about(request):
    return render(request,'about.html',{})

def login_user(request):
    if request.method=="POST":
        username = request.POST['username']
        password =request.POST['password']
        user =  authenticate(request,username=username,password=password)
        if user is not None:
            login(request,user)
            messages.success(request,"Welcome....")
            return redirect('home')
        else:
            messages.success(request,("Something went wrong...."))
            return redirect('login')
    else:
        return render(request,'profile/login.html',{})


    return render(request,'login.html',{})

def logout_user(request):
    logout(request)
    messages.success(request,"You have been loged out ...")
    return redirect('home')

def register_user(request):
    form= SignUpForm()
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password1"]
            user = authenticate(username=username, password=password)
            login(request, user)
            messages.success(
                request,
            "Great, your account is successfully registered. Please complete your personal information.",
            )
            return redirect('home')
    else:
        messages.error(
                request,
                "Oops something went wrong with your registration, please try again.",
            )
        return render(request,'profile/register.html',{'form':form})

def search(request):
    if request.method == "POST":
        searched = request.POST["q"]
        searched = Product.objects.filter(
            Q(name__icontains=searched) |
            Q(description__icontains=searched) 
        )
        if not searched: 
            messages.info(request, "That product does not exist, please try again.")
            return render(request, "product/search.html", {})
        else:
            context = {"searched": searched}
            return render(request, "product/search.html", context)
    else:
        context = {}
        return render(request, "product/search.html", context)

def new_arrivals(request):
    new_products = Product.objects.all().order_by('-id')[:10]  # Fetch latest 10 products
    return render(request, 'product/new_arrivals.html', {'new_products': new_products})


@login_required
@require_GET
def get_recommendations(request):
    product_id = request.GET.get('product_id')

    if not product_id:
        return JsonResponse({"error": "product_id is required"}, status=400)

    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return JsonResponse({"error": "Product not found"}, status=404)

    # Exclude the current product
    other_products = list(Product.objects.exclude(id=product.id))

    # Gather embeddings of other products (assumes embeddings are stored as lists)
    embeddings = [p.embedding for p in other_products if p.embedding]

    if not product.embedding or not embeddings:
        return JsonResponse({"recommendations": []})

    try:
        # Make request to FastAPI for recommendations
        response = requests.post(
            f"{FASTAPI_URL}/recommend",
            json={
                "target_embedding": product.embedding,
                "all_embeddings": embeddings
            }
        )
        response.raise_for_status()
        recommended_indices = response.json().get("recommended_ids", [])
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

    # Ensure indices are within range
    recommended_products = [
        other_products[i] for i in recommended_indices if i < len(other_products)
    ]

    # Return recommended products as JSON
    return JsonResponse({
        "recommendations": [
            {"id": p.id, "name": p.name, "price": float(p.price)}
            for p in recommended_products
        ]
    })


def track_recommendation_click(request):
    try:
        log_id = request.POST.get('log_id')
        source_product_id = request.POST.get('source_product_id')
        recommended_product_id = request.POST.get('recommended_product_id')
        
        if log_id:
            log = RecommendationLog.objects.get(id=log_id)
            log.clicked = True
            log.save()
        
        return redirect('product', pk=recommended_product_id)
    
    except Exception as e:
        # Fallback if tracking fails
        return redirect('product', pk=recommended_product_id)
    
@login_required
def delete_review(request, review_id):
    review = get_object_or_404(ProductReview, id=review_id, user=request.user)
    product_id = review.product.id
    review.delete()
    messages.success(request, "Your review has been deleted.")
    return redirect('product', pk=product_id)
    
