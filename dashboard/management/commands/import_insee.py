import csv
from django.core.management.base import BaseCommand
from dashboard.models import Population
from django.db import transaction

class Command(BaseCommand):
    help = 'Importe les données de population INSEE depuis un CSV'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Chemin vers le fichier CSV')

    def handle(self, *args, **options):
        path = options['csv_file']
        
        try:
            with open(path, 'r', encoding='utf-8-sig') as f:
                # 1. Detect delimiter (INSEE usually uses ';')
                sample = f.readline()
                dialect = ';' if ';' in sample else ','
                f.seek(0)
                
                reader = csv.DictReader(f, delimiter=dialect)
                self.stdout.write(f"Detected columns: {reader.fieldnames}")
                
                objs = []
                for row in reader:
                    # We use .get() to prevent crashes if a column is missing
                    # and replace spaces in the population number
                    try:
                        population_value = str(row.get('PMUN', '0')).replace(' ', '').strip()
                        
                        objs.append(
                            Population(
                                reg=row.get('REG', ''),
                                region=row.get('Région', ''),
                                dep=row.get('DEP', ''),
                                departement=row.get('Département', ''),
                                pop=int(population_value) if population_value.isdigit() else 0
                            )
                        )
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f"Skipping row: {e}"))

                # 2. Database Transaction
                if objs:
                    self.stdout.write(f"Found {len(objs)} rows. Starting import...")
                    
                    # This clears the table first to avoid duplicates if you re-run it
                    Population.objects.all().delete()
                    
                    # Bulk create is much faster than individual .save() calls
                    created = Population.objects.bulk_create(objs)
                    
                    self.stdout.write(
                        self.style.SUCCESS(f"Successfully imported {len(created)} departments!")
                    )
                else:
                    self.stdout.write(self.style.ERROR("No data found in CSV."))

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"File not found at: {path}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"An error occurred: {e}"))