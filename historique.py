"""
Module pour gérer l'historique des modifications
"""

import sqlite3
from datetime import datetime
from database import DB_NAME
import json

def ajouter_historique(type_action, table_concernee, id_enregistrement, details, ancienne_valeur=None, nouvelle_valeur=None, utilisateur='admin'):
    """
    Ajoute une entrée dans l'historique
    
    Args:
        type_action: 'CREATE', 'UPDATE', 'DELETE'
        table_concernee: 'participants', 'cotisations'
        id_enregistrement: ID de l'enregistrement modifié
        details: Description de l'action
        ancienne_valeur: Valeur avant modification (JSON)
        nouvelle_valeur: Valeur après modification (JSON)
        utilisateur: Nom de l'utilisateur (par défaut 'admin')
    """
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        date_action = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Convertir les valeurs en JSON si ce sont des dictionnaires
        if isinstance(ancienne_valeur, dict):
            ancienne_valeur = json.dumps(ancienne_valeur, ensure_ascii=False)
        if isinstance(nouvelle_valeur, dict):
            nouvelle_valeur = json.dumps(nouvelle_valeur, ensure_ascii=False)
        
        cursor.execute("""
            INSERT INTO historique (date_action, utilisateur, type_action, table_concernee, 
                                   id_enregistrement, details, ancienne_valeur, nouvelle_valeur)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (date_action, utilisateur, type_action, table_concernee, id_enregistrement, 
              details, ancienne_valeur, nouvelle_valeur))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Erreur lors de l'ajout à l'historique: {e}")
        return False

def get_historique(limit=50, table_concernee=None, type_action=None):
    """
    Récupère l'historique des modifications
    
    Args:
        limit: Nombre maximum d'entrées à retourner
        table_concernee: Filtrer par table (optionnel)
        type_action: Filtrer par type d'action (optionnel)
    
    Returns:
        Liste de tuples avec les données de l'historique
    """
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        query = "SELECT * FROM historique WHERE 1=1"
        params = []
        
        if table_concernee:
            query += " AND table_concernee = ?"
            params.append(table_concernee)
        
        if type_action:
            query += " AND type_action = ?"
            params.append(type_action)
        
        query += " ORDER BY date_action DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        conn.close()
        return results
    except Exception as e:
        print(f"Erreur lors de la récupération de l'historique: {e}")
        return []

def get_historique_participant(participant_id, limit=20):
    """
    Récupère l'historique d'un participant spécifique
    """
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM historique 
            WHERE (table_concernee = 'participants' AND id_enregistrement = ?)
               OR (table_concernee = 'cotisations' AND details LIKE ?)
            ORDER BY date_action DESC 
            LIMIT ?
        """, (participant_id, f"%participant_id={participant_id}%", limit))
        
        results = cursor.fetchall()
        conn.close()
        return results
    except Exception as e:
        print(f"Erreur lors de la récupération de l'historique du participant: {e}")
        return []
