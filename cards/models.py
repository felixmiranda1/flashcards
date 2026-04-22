from django.db import models
from django.urls import reverse
from django.utils import timezone


class Category(models.Model):
    name = models.CharField("nome", max_length=120, unique=True)
    description = models.TextField("descricao", blank=True)
    created_at = models.DateTimeField("criado em", auto_now_add=True)
    updated_at = models.DateTimeField("atualizado em", auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "categoria"
        verbose_name_plural = "categorias"

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("cards:category_detail", args=[self.pk])


class Flashcard(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="flashcards",
        verbose_name="categoria",
    )
    question = models.TextField("pergunta")
    answer = models.TextField("resposta")
    priority = models.PositiveSmallIntegerField(
        "prioridade",
        default=3,
        help_text="1 = baixa, 5 = alta",
    )
    correct_count = models.PositiveIntegerField("acertos", default=0)
    wrong_count = models.PositiveIntegerField("erros", default=0)
    last_studied_at = models.DateTimeField("ultimo estudo", null=True, blank=True)
    created_at = models.DateTimeField("criado em", auto_now_add=True)
    updated_at = models.DateTimeField("atualizado em", auto_now=True)

    class Meta:
        ordering = ["category__name", "question"]
        verbose_name = "flashcard"
        verbose_name_plural = "flashcards"

    def __str__(self):
        return self.question[:80]

    @property
    def total_attempts(self):
        return self.correct_count + self.wrong_count

    @property
    def accuracy_percent(self):
        if not self.total_attempts:
            return None
        return round((self.correct_count / self.total_attempts) * 100)

    @property
    def study_score(self):
        # Heuristica simples: erros e prioridade puxam a carta para frente.
        base = self.priority * 2
        return base + (self.wrong_count * 3) - self.correct_count

    def register_result(self, is_correct):
        if is_correct:
            self.correct_count = models.F("correct_count") + 1
        else:
            self.wrong_count = models.F("wrong_count") + 1
        self.last_studied_at = timezone.now()
        self.save(update_fields=["correct_count", "wrong_count", "last_studied_at", "updated_at"])


class StudyAttempt(models.Model):
    class Result(models.TextChoices):
        PENDING = "pending", "pendente"
        CORRECT = "correct", "acertei"
        WRONG = "wrong", "errei"

    flashcard = models.ForeignKey(
        Flashcard,
        on_delete=models.CASCADE,
        related_name="attempts",
        verbose_name="flashcard",
    )
    typed_answer = models.TextField("resposta digitada")
    result = models.CharField(
        "resultado",
        max_length=10,
        choices=Result.choices,
        default=Result.PENDING,
    )
    response_time_seconds = models.PositiveIntegerField("tempo de resposta", null=True, blank=True)
    created_at = models.DateTimeField("respondido em", auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "tentativa"
        verbose_name_plural = "tentativas"

    def __str__(self):
        return f"{self.flashcard_id} - {self.get_result_display()}"
