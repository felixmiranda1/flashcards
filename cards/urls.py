from django.urls import path

from . import views

app_name = "cards"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("categorias/", views.category_list, name="category_list"),
    path("categorias/nova/", views.category_create, name="category_create"),
    path("categorias/<int:pk>/", views.category_detail, name="category_detail"),
    path("flashcards/novo/", views.flashcard_create, name="flashcard_create"),
    path("estudar/", views.study, name="study"),
    path("estudar/menu/", views.study_menu, name="study_menu"),
    path("estudar/<int:flashcard_id>/responder/", views.submit_answer, name="submit_answer"),
    path("tentativas/<int:attempt_id>/resultado/", views.mark_attempt_result, name="mark_attempt_result"),
]
