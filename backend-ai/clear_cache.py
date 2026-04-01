"""
Script à exécuter UNE FOIS pour vider le cache shelve.
Le cache garde les anciens snippets à 1000 chars — sans le vider,
competitor_tools.py retournera toujours les vieux résultats.

Usage : python clear_cache.py
"""
import os
import shelve
import tempfile
import glob

CACHE_FILE = os.path.join(tempfile.gettempdir(), "ma_cache")

# Supprimer tous les fichiers shelve (.db, .dir, .bak, .dat)
deleted = 0
for f in glob.glob(CACHE_FILE + "*"):
    try:
        os.remove(f)
        print(f"✅ Supprimé : {f}")
        deleted += 1
    except Exception as e:
        print(f"❌ Erreur : {f} — {e}")

if deleted == 0:
    print("ℹ️  Aucun fichier cache trouvé — déjà vide.")
else:
    print(f"\n✅ Cache vidé ({deleted} fichiers supprimés)")
    print("   Le prochain run rechargera les données depuis les APIs.")
