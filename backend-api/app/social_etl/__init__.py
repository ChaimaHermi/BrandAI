"""Pipeline ETL des metriques sociales (Facebook, Instagram, LinkedIn).

Hebergé dans backend-api : seul service ayant un acces direct a la base de donnees.
Declenche par les routes optimizer, consomme par l'agent Optimizer (backend-ai)
via les endpoints REST.
"""
