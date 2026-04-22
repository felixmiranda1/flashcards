import random
import time
from datetime import timedelta

from django.contrib import messages
from django.db.models import Count, Q
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import CategoryForm, FlashcardForm, StudyAnswerForm
from .models import Category, Flashcard, StudyAttempt


def dashboard(request):
    categories = Category.objects.annotate(card_count=Count("flashcards"))[:6]
    total_cards = Flashcard.objects.count()
    evaluated_attempts = StudyAttempt.objects.exclude(result=StudyAttempt.Result.PENDING)
    total_attempts = evaluated_attempts.count()
    total_correct = evaluated_attempts.filter(result=StudyAttempt.Result.CORRECT).count()
    total_wrong = evaluated_attempts.filter(result=StudyAttempt.Result.WRONG).count()
    accuracy_rate = round((total_correct / total_attempts) * 100) if total_attempts else 0

    today = timezone.localdate()
    recent_cutoff = timezone.now() - timedelta(days=7)
    previous_cutoff = timezone.now() - timedelta(days=14)
    recent_attempts_count = evaluated_attempts.filter(created_at__gte=recent_cutoff).count()
    previous_attempts_count = evaluated_attempts.filter(created_at__gte=previous_cutoff, created_at__lt=recent_cutoff).count()
    recent_correct = evaluated_attempts.filter(result=StudyAttempt.Result.CORRECT, created_at__gte=recent_cutoff).count()
    recent_accuracy = round((recent_correct / recent_attempts_count) * 100) if recent_attempts_count else 0

    studied_dates = {
        timezone.localtime(attempt.created_at).date()
        for attempt in evaluated_attempts.only("created_at")[:200]
    }
    current_streak = 0
    day = today
    while day in studied_dates:
        current_streak += 1
        day -= timedelta(days=1)

    category_focus = []
    for category in Category.objects.annotate(
        card_count=Count("flashcards", distinct=True),
        attempts_count=Count(
            "flashcards__attempts",
            filter=~Q(flashcards__attempts__result=StudyAttempt.Result.PENDING),
            distinct=True,
        ),
        correct_count=Count(
            "flashcards__attempts",
            filter=Q(flashcards__attempts__result=StudyAttempt.Result.CORRECT),
            distinct=True,
        ),
        wrong_count=Count(
            "flashcards__attempts",
            filter=Q(flashcards__attempts__result=StudyAttempt.Result.WRONG),
            distinct=True,
        ),
    ):
        if category.attempts_count:
            category.accuracy = round((category.correct_count / category.attempts_count) * 100)
        else:
            category.accuracy = None
        category_focus.append(category)
    category_focus.sort(key=lambda item: (item.accuracy is None, item.accuracy or 0, -item.wrong_count))

    recent_attempts = evaluated_attempts.select_related("flashcard", "flashcard__category")[:6]
    due_cards = sorted(Flashcard.objects.all(), key=lambda card: card.study_score, reverse=True)[:5]
    focus_category = next((category for category in category_focus if category.wrong_count), None)
    if not total_attempts:
        insight_message = "Comece com uma sessao curta. Cinco cards ja criam um bom ponto de partida."
    elif focus_category:
        insight_message = f"Vale revisar mais {focus_category.name}: ela concentra {focus_category.wrong_count} erro(s)."
    elif recent_attempts_count > previous_attempts_count:
        insight_message = "Seu ritmo subiu nesta semana. Boa hora para manter a sequencia."
    elif accuracy_rate >= 75:
        insight_message = "Voce esta indo bem. Continue revisando os cards de maior prioridade."
    else:
        insight_message = "A base ja esta registrada. Foque nos cards com mais erros para subir a taxa."

    return render(
        request,
        "cards/dashboard.html",
        {
            "categories": categories,
            "total_cards": total_cards,
            "total_attempts": total_attempts,
            "total_correct": total_correct,
            "total_wrong": total_wrong,
            "accuracy_rate": accuracy_rate,
            "recent_accuracy": recent_accuracy,
            "recent_attempts_count": recent_attempts_count,
            "current_streak": current_streak,
            "category_focus": category_focus[:4],
            "recent_attempts": recent_attempts,
            "due_cards": due_cards,
            "insight_message": insight_message,
        },
    )


def category_list(request):
    categories = Category.objects.annotate(card_count=Count("flashcards"))
    return render(request, "cards/category_list.html", {"categories": categories})


def category_create(request):
    form = CategoryForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        category = form.save()
        messages.success(request, "Categoria criada.")
        return redirect(category)
    return render(request, "cards/category_form.html", {"form": form})


def category_detail(request, pk):
    category = get_object_or_404(Category.objects.annotate(card_count=Count("flashcards")), pk=pk)
    flashcards = category.flashcards.all().order_by("-wrong_count", "question")
    return render(request, "cards/category_detail.html", {"category": category, "flashcards": flashcards})


def flashcard_create(request):
    if not Category.objects.exists():
        messages.info(request, "Crie uma categoria antes de cadastrar flashcards.")
        return redirect("cards:category_create")

    form = FlashcardForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Flashcard criado.")
        return redirect("cards:dashboard")
    return render(request, "cards/flashcard_form.html", {"form": form})


def study(request):
    category_id = request.GET.get("category")
    mode = request.GET.get("mode", "smart")
    study_qs = _study_queryset(category_id=category_id)
    total_filtered_cards = study_qs.count()
    studied_filtered_cards = study_qs.filter(last_studied_at__isnull=False).count()
    progress_current = min(studied_filtered_cards + 1, total_filtered_cards) if total_filtered_cards else 0
    flashcard = _pick_flashcard(category_id=category_id, mode=mode)
    categories = Category.objects.annotate(card_count=Count("flashcards")).filter(card_count__gt=0)
    form = StudyAnswerForm(initial={"started_at": time.time()})
    return render(
        request,
        "cards/study.html",
        {
            "categories": categories,
            "selected_category": category_id or "",
            "mode": mode,
            "flashcard": flashcard,
            "form": form,
            "progress_current": progress_current,
            "total_filtered_cards": total_filtered_cards,
        },
    )


def study_menu(request):
    if request.GET.get("state") == "closed":
        return render(request, "cards/partials/study_drawer_closed.html")

    selected_category = request.GET.get("category", "")
    mode = request.GET.get("mode", "smart")
    categories = Category.objects.annotate(card_count=Count("flashcards")).filter(card_count__gt=0)
    return render(
        request,
        "cards/partials/study_drawer.html",
        {
            "categories": categories,
            "selected_category": selected_category,
            "mode": mode,
        },
    )


@require_POST
def submit_answer(request, flashcard_id):
    flashcard = get_object_or_404(Flashcard, pk=flashcard_id)
    form = StudyAnswerForm(request.POST)
    if not form.is_valid():
        return render(
            request,
            "cards/partials/study_answer_form.html",
            {
                "flashcard": flashcard,
                "form": form,
                "selected_category": request.POST.get("category", ""),
                "mode": request.POST.get("mode", "smart"),
            },
            status=400,
        )

    started_at = form.cleaned_data["started_at"]
    elapsed = max(0, int(time.time() - started_at))
    attempt = StudyAttempt.objects.create(
        flashcard=flashcard,
        typed_answer=form.cleaned_data["typed_answer"],
        response_time_seconds=elapsed,
    )
    return render(
        request,
        "cards/partials/reveal_answer.html",
        {
            "attempt": attempt,
            "flashcard": flashcard,
            "selected_category": request.POST.get("category", ""),
            "mode": request.POST.get("mode", "smart"),
        },
    )


@require_POST
def mark_attempt_result(request, attempt_id):
    attempt = get_object_or_404(StudyAttempt.objects.select_related("flashcard"), pk=attempt_id)
    result = request.POST.get("result")
    if result not in {StudyAttempt.Result.CORRECT, StudyAttempt.Result.WRONG}:
        return HttpResponseBadRequest("Resultado invalido.")

    if attempt.result == StudyAttempt.Result.PENDING:
        attempt.result = result
        attempt.save(update_fields=["result"])
        attempt.flashcard.register_result(is_correct=result == StudyAttempt.Result.CORRECT)

    category = request.POST.get("category", "")
    mode = request.POST.get("mode", "smart")
    next_url = f"{reverse('cards:study')}?mode={mode}"
    if category:
        next_url += f"&category={category}"
    response = render(request, "cards/partials/result_saved.html", {"attempt": attempt, "next_url": next_url})
    response["HX-Redirect"] = next_url
    return response


def _pick_flashcard(category_id=None, mode="smart"):
    qs = _study_queryset(category_id=category_id).select_related("category")

    if mode == "order":
        return qs.order_by("last_studied_at", "category__name", "question").first()

    if mode == "random":
        ids = list(qs.values_list("id", flat=True))
        if not ids:
            return None
        return qs.get(id=random.choice(ids))

    cards = list(qs)
    if not cards:
        return None
    cards.sort(key=lambda card: card.study_score, reverse=True)
    top_window = cards[: min(len(cards), 5)]
    return random.choice(top_window)


def _study_queryset(category_id=None):
    qs = Flashcard.objects.all()
    if category_id:
        qs = qs.filter(category_id=category_id)
    return qs
