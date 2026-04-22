from django.contrib import admin

from .models import Category, Flashcard, StudyAttempt


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "created_at"]
    search_fields = ["name"]


@admin.register(Flashcard)
class FlashcardAdmin(admin.ModelAdmin):
    list_display = ["question", "category", "priority", "correct_count", "wrong_count", "last_studied_at"]
    list_filter = ["category", "priority"]
    search_fields = ["question", "answer"]


@admin.register(StudyAttempt)
class StudyAttemptAdmin(admin.ModelAdmin):
    list_display = ["flashcard", "result", "response_time_seconds", "created_at"]
    list_filter = ["result", "created_at"]
    search_fields = ["typed_answer", "flashcard__question"]
