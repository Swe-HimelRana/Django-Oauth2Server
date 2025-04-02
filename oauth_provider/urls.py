from django.urls import path
from . import views


urlpatterns = [
    path('authorize/', views.authorize, name='authorize'),
    path('token/', views.token, name='token'),
    path('userinfo/', views.userinfo, name='userinfo'),
    path('logout/', views.logout, name='oauth_logout'),
    path('userdata/<int:user_id>/', views.userdata, name='userdata'),
    
    
]