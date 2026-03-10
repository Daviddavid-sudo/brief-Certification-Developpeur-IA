from django.db import models

class MeteoArchive(models.Model):
    ville = models.CharField(max_length=100)
    annee = models.IntegerField()
    mois = models.IntegerField()
    jour = models.IntegerField()
    temp_max = models.FloatField()
    temp_min = models.FloatField()

    class Meta:
        unique_together = ('ville', 'annee', 'mois', 'jour')

class ActiviteCommerciale(models.Model):
    # Ajout du champ manquant pour la carte
    code_dept = models.CharField(max_length=3, default='00') 
    bv2022 = models.CharField(max_length=50)
    ville = models.CharField(max_length=100)
    ca_tot = models.FloatField()
    mois = models.IntegerField()
    annee = models.IntegerField()

    class Meta:
        unique_together = ('ville', 'annee', 'mois')


class Population(models.Model):
    reg = models.CharField(max_length=5, help_text="Code de la région")
    region = models.CharField(max_length=100)
    dep = models.CharField(max_length=5, unique=True, help_text="Code du département (ex: 75, 2A)")
    departement = models.CharField(max_length=100)
    pop = models.IntegerField(verbose_name="Population municipale (PMUN)")
    date_import = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Donnée Population"
        verbose_name_plural = "Données Population"
        ordering = ['dep'] # Trie par numéro de département par défaut

    def __str__(self):
        return f"{self.dep} - {self.departement} ({self.pop} hab.)"