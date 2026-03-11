import csv
import os
from django.core.management.base import BaseCommand
from dashboard.models import Population

class Command(BaseCommand):
    help = 'Importe les données de population INSEE depuis un CSV'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str)

    def handle(self, *args, **options):
        path = options['csv_file']
        
        if not os.path.exists(path):
            self.stdout.write(self.style.ERROR(f"File not found at: {path}"))
            return

        try:
            with open(path, 'r', encoding='utf-8-sig') as f:
                # Detect if the separator is ; or ,
                line = f.readline()
                dialect = ';' if ';' in line else ','
                f.seek(0)
                
                reader = csv.DictReader(f, delimiter=dialect)
                objs = []
                
                for row in reader:
                    # Logic to find the population column regardless of name
                    pop_val = row.get('PMUN') or row.get('pop') or row.get('population') or '0'
                    # Remove spaces (e.g., "65 000" -> 65000)
                    clean_pop = "".join(filter(str.isdigit, str(pop_val)))

                    objs.append(Population(
                        reg=row.get('REG', ''),
                        region=row.get('Région', row.get('region', '')),
                        dep=row.get('DEP', ''),
                        departement=row.get('Département', row.get('departement', '')),
                        pop=int(clean_pop) if clean_pop else 0
                    ))

                if objs:
                    Population.objects.all().delete()
                    Population.objects.bulk_create(objs)
                    self.stdout.write(self.style.SUCCESS(f"✅ Succès : {len(objs)} lignes importées !"))
                else:
                    self.stdout.write(self.style.ERROR("Le CSV semble vide ou mal formaté."))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Erreur lors de l'import : {e}"))