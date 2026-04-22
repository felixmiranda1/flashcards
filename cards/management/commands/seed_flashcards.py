from django.core.management.base import BaseCommand

from cards.models import Category, Flashcard


SAMPLE_DATA = {
    "Cardiologia": [
        (
            "Qual e a conduta inicial em suspeita de IAM com supra de ST?",
            "Reconhecer rapidamente, acionar reperfusao imediata, administrar AAS se nao houver contraindicao e seguir protocolo institucional.",
            5,
        ),
        (
            "Quais sinais sugerem insuficiencia cardiaca descompensada?",
            "Dispneia, ortopneia, edema periferico, estertores, turgencia jugular e ganho de peso recente.",
            4,
        ),
    ],
    "Infectologia": [
        (
            "Qual e a principal medida inicial em sepse suspeita?",
            "Coletar culturas quando possivel sem atrasar antibiotico, iniciar antibiotico precoce, medir lactato e ressuscitar conforme perfusao.",
            5,
        ),
        (
            "Quando suspeitar de meningite bacteriana?",
            "Febre, cefaleia, rigidez de nuca, alteracao do estado mental ou sinais de irritacao meningea.",
            4,
        ),
    ],
    "Pediatria": [
        (
            "Qual e a prioridade no atendimento inicial da crianca grave?",
            "Avaliar rapidamente via aerea, respiracao, circulacao, estado neurologico e exposicao, corrigindo ameacas imediatas.",
            5,
        ),
    ],
}


class Command(BaseCommand):
    help = "Cria categorias e flashcards de exemplo para testar o MVP."

    def handle(self, *args, **options):
        created_cards = 0
        for category_name, cards in SAMPLE_DATA.items():
            category, _ = Category.objects.get_or_create(name=category_name)
            for question, answer, priority in cards:
                _, created = Flashcard.objects.get_or_create(
                    category=category,
                    question=question,
                    defaults={"answer": answer, "priority": priority},
                )
                created_cards += int(created)

        self.stdout.write(self.style.SUCCESS(f"Seed concluido. {created_cards} flashcards criados."))
