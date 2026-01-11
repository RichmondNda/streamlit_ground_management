"""
Script de sauvegarde automatique de la base de données
"""

import shutil
import os
from datetime import datetime

DB_NAME = "database.db"
BACKUP_DIR = "backups"

def backup_database():
    """Crée une copie de sauvegarde de la base de données"""
    # Créer le dossier de backup s'il n'existe pas
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
    
    # Vérifier que la base existe
    if not os.path.exists(DB_NAME):
        print(f"Erreur: La base de données {DB_NAME} n'existe pas")
        return False
    
    # Créer le nom du fichier de backup avec timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{BACKUP_DIR}/database_backup_{timestamp}.db"
    
    try:
        # Copier la base de données
        shutil.copy2(DB_NAME, backup_name)
        print(f"✅ Backup créé: {backup_name}")
        
        # Nettoyer les anciens backups (garder seulement les 10 derniers)
        cleanup_old_backups()
        
        return True
    except Exception as e:
        print(f"❌ Erreur lors du backup: {str(e)}")
        return False

def cleanup_old_backups(keep=10):
    """Supprime les anciens backups en gardant seulement les N derniers"""
    if not os.path.exists(BACKUP_DIR):
        return
    
    # Lister tous les fichiers de backup
    backups = [f for f in os.listdir(BACKUP_DIR) if f.startswith("database_backup_") and f.endswith(".db")]
    backups.sort(reverse=True)  # Trier par ordre décroissant (plus récent d'abord)
    
    # Supprimer les backups en trop
    for old_backup in backups[keep:]:
        try:
            os.remove(os.path.join(BACKUP_DIR, old_backup))
            print(f"🗑️  Ancien backup supprimé: {old_backup}")
        except Exception as e:
            print(f"⚠️  Impossible de supprimer {old_backup}: {str(e)}")

if __name__ == "__main__":
    backup_database()
