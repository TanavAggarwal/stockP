from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.login, name='login'),
    path('index.html/', views.index, name='index'),
    path('save/', views.save_data, name='save'),
    path('save2/', views.save_data2, name='save2'),
    path('login.html/', views.login, name='login'),
    path('logout.html/', views.logout, name='logout'),
    path('register.html/', views.register, name='register'),
    path('password.html/', views.password, name='password'),
    path('charts.html/', views.charts, name='charts'),
    path('predictor.html/', views.predictor, name='predictor'),
    path('refresh_charts.html/', views.refresh_charts, name='refresh_charts'),
    path('refresh_funds.html/', views.refresh_funds, name='refresh_funds'),
    #path('mfh_charts.html/', views.mfh_charts, name='mfh_charts'),
    path('mfunds.html/', views.mfunds, name='mfunds'),
    path('mfholding.html/', views.mfholding, name='mfholding'),
]
