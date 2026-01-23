"""
URL configuration for supportticket project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from ticket.views import TicketViewSet, CommentViewSet, WebhookViewSet
import user.views as user_views

# Create a router and register our viewsets
router = DefaultRouter()
router.register(r'tickets', TicketViewSet, basename='ticket')
router.register(r'comments', CommentViewSet, basename='comment')
router.register(r'webhooks', WebhookViewSet, basename='webhook')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/auth/register/', user_views.register_view, name='api_register'),
    path('api/auth/login/', user_views.login_view, name='api_login'),
    path('api/auth/logout/', user_views.logout_view, name='api_logout'),
    path('api/auth/user/', user_views.current_user_view, name='api_current_user'),
]
