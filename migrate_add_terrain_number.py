"""
Script de migration pour ajouter la colonne numero_terrain à la table cotisations
"""

import sqlite3
from database import DB_NAME

def migrate():
    """Ajoute la colonne numero_terrain à la table cotisations"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    try:
        # Vérifier si la colonne existe déjà
        cursor.execute("PRAGMA table_info(cotisations)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'numero_terrain' in columns:
            print("✅ La colonne 'numero_terrain' existe déjà.")
            return
        
        print("🔄 Ajout de la colonne 'numero_terrain'...")
        
        # Ajouter la colonne
        cursor.execute("ALTER TABLE cotisations ADD COLUMN numero_terrain INTEGER")
        
        # Les cotisations existantes auront NULL pour numero_terrain
        # ce qui signifie "tous les terrains" (répartition équitable)
        
        conn.commit()
        print("✅ Migration terminée avec succès!")
        print("ℹ️  Les cotisations existantes auront NULL pour le numéro de terrain (= tous les terrains)")
        
    except Exception as e:
        print(f"❌ Erreur lors de la migration: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
