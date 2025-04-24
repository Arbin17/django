from django.urls import path,include

from . import views
urlpatterns = [
   
   path('',views.home,name='home'),
   path('about/',views.about,name='about'),
   path('login/',views.login_user,name='login'),
   path('logout/',views.logout_user,name='logout'),
   path('register/', views.register_user, name='register'),
   path('product/<int:pk>/', views.product, name='product'),
   path('search/', views.search, name='search'),
   path('new-arrivals/', views.new_arrivals, name='new_arrivals'),
   path('get-recommendations/', views.get_recommendations, name='get_recommendations'),
   path('track-recommendation/', views.track_recommendation_click, name='track_recommendation_click'),
   path('review/delete/<int:review_id>/', views.delete_review, name='delete_review'),
   path('catogery/<str:ak>/', views.catogery, name='catogery'),
   
  
]
