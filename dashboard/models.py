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