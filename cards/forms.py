from django import forms

from .models import Category, Flashcard


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name", "description"]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Ex.: Cardiologia"}),
            "description": forms.Textarea(attrs={"rows": 3, "placeholder": "Opcional"}),
        }


class FlashcardForm(forms.ModelForm):
    class Meta:
        model = Flashcard
        fields = ["category", "question", "answer", "priority"]
        widgets = {
            "question": forms.Textarea(attrs={"rows": 4, "placeholder": "Digite a pergunta"}),
            "answer": forms.Textarea(attrs={"rows": 5, "placeholder": "Digite o gabarito"}),
            "priority": forms.NumberInput(attrs={"min": 1, "max": 5}),
        }


class StudyAnswerForm(forms.Form):
    typed_answer = forms.CharField(
        label="Sua resposta",
        widget=forms.Textarea(
            attrs={
                "rows": 7,
                "placeholder": "Escreva sua resposta antes de ver o gabarito...",
                "autofocus": "autofocus",
            }
        ),
    )
    started_at = forms.FloatField(widget=forms.HiddenInput)
