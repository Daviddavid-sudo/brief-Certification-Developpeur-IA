from django.core.management.base import BaseCommand
from dashboard.services import ask_llm_about_db

class Command(BaseCommand):
    help = "Teste le service LangChain/Groq"

    def add_arguments(self, parser):
        parser.add_argument('question', type=str)

    def handle(self, *args, **options):
        question = options['question']
        self.stdout.write(f"Question: {question}")
        
        # Call your service
        reponse = ask_llm_about_db(question)
        
        self.stdout.write(self.style.SUCCESS(f"Réponse: {reponse}"))