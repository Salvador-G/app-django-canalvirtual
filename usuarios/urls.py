from django.urls import path
from .views import LoginView, UsuarioView, UsuarioPorIdView

urlpatterns = [
    path('login', LoginView.as_view()),
    path('usuario', UsuarioView.as_view()),
    path('usuario/<int:id>', UsuarioPorIdView.as_view()),
]
