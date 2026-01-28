import user.views as user_views
from django.urls import path



urlpatterns = [
    path('register/', user_views.register_view, name='api_register'),
    path('login/', user_views.login_view, name='api_login'),
    path('logout/', user_views.logout_view, name='api_logout'),
    path('user/', user_views.current_user_view, name='api_current_user'),
]