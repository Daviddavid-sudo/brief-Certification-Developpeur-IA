from django.core.management.base import BaseCommand
from dashboard.models import ActiviteCommerciale, Population

class Command(BaseCommand):
    help = 'Clears table and seeds CA data with strong seasonality (1.0x vs 3.0x)'

    def get_seasonality_multiplier(self, month):
        # Stronger seasonality: Summer (June-August) at 3.0, Others at 1.0
        if month in [6, 7, 8]:
            return 3.0
        return 1.0

    def calculate_ca(self, population_count, month):
        # Under 100k remains 0
        if population_count < 100000:
            return 0
        
        base_ca = population_count * 2
        multiplier = self.get_seasonality_multiplier(month)
        return int(base_ca * multiplier)

    def handle(self, *args, **options):
        target_year = 2024
        
        # 1. Clear the existing data
        self.stdout.write(self.style.WARNING('Clearing existing ActiviteCommerciale data...'))
        ActiviteCommerciale.objects.all().delete()
        
        all_depts = Population.objects.all()
        if not all_depts.exists():
            self.stdout.write(self.style.ERROR('The Population table is empty!'))
            return

        self.stdout.write(self.style.NOTICE(f'Starting fresh sync for {target_year}...'))

        # 2. Seed data for the full year
        for month in range(1, 13):
            entries = []
            for p in all_depts:
                ca_result = self.calculate_ca(p.pop, month)
                
                # Using bulk_create or update_or_create. 
                # Since we deleted all, create is faster.
                entries.append(ActiviteCommerciale(
                    code_dept=p.dep,
                    annee=target_year,
                    mois=month,
                    ville=p.departement,
                    ca_tot=ca_result,
                    bv2022=f"{p.dep}000"
                ))
            
            ActiviteCommerciale.objects.bulk_create(entries)
            self.stdout.write(f"Mois {month}: Multiplier {self.get_seasonality_multiplier(month)}x applied.")

        self.stdout.write(self.style.SUCCESS('Seeding complete. Seasonality is now set to 1.0x (Regular) and 3.0x (Summer).'))