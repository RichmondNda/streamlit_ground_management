"""
Page Relances WhatsApp - Génération de messages personnalisés
"""

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import urllib.parse
from database import DB_NAME
from constants import MOIS_NOMS
from auth import require_authentication, show_logout_button
from historique import ajouter_historique

# Configuration de la page
st.set_page_config(
    page_title="Relances WhatsApp - MEDD",
    page_icon="📱",
    layout="wide"
)

# Vérifier l'authentification
require_authentication()

# Afficher le bouton de déconnexion
show_logout_button()

# ============================================================================
# FONCTIONS
# ============================================================================

def get_participants_impayees():
    """Récupère les participants avec des cotisations impayées"""
    conn = sqlite3.connect(DB_NAME)
    
    df = pd.read_sql_query("""
        SELECT 
            p.id,
            p.nom,
            p.prenom,
            p.telephone,
            p.email,
            COUNT(c.id) as nb_impayees,
            SUM(c.montant) as montant_total,
            GROUP_CONCAT(DISTINCT c.annee || '-' || c.mois) as periodes
        FROM participants p
        JOIN cotisations c ON p.id = c.participant_id
        WHERE c.paye = 0 AND p.telephone IS NOT NULL AND p.telephone != ''
        GROUP BY p.id
        ORDER BY montant_total DESC
    """, conn)
    
    conn.close()
    return df

def get_details_impayees(participant_id):
    """Récupère le détail des cotisations impayées pour un participant"""
    conn = sqlite3.connect(DB_NAME)
    
    df = pd.read_sql_query("""
        SELECT 
            mois,
            annee,
            montant,
            numero_terrain
        FROM cotisations
        WHERE participant_id = ? AND paye = 0
        ORDER BY annee, mois, numero_terrain
    """, conn, params=(participant_id,))
    
    conn.close()
    return df

def generer_message_whatsapp(nom, prenom, details_impayees, montant_total):
    """Génère un message WhatsApp personnalisé"""
    
    message = f"Bonjour {prenom} {nom},\n\n"
    message += "🏞️ **Rappel Cotisations MEDD**\n\n"
    message += f"Nous vous rappelons que vous avez {len(details_impayees)} cotisation(s) en attente de paiement:\n\n"
    
    # Grouper par mois
    for _, row in details_impayees.iterrows():
        mois_nom = MOIS_NOMS[int(row['mois']) - 1]
        terrain_info = f" (Terrain n°{int(row['numero_terrain'])})" if pd.notna(row['numero_terrain']) else ""
        message += f"• {mois_nom} {int(row['annee'])}{terrain_info}: {row['montant']:,.0f} FCFA\n".replace(',', ' ')
    
    message += f"\n💰 **Total à payer: {montant_total:,.0f} FCFA**\n\n".replace(',', ' ')
    message += "Merci de régulariser votre situation dans les meilleurs délais.\n\n"
    message += "Pour toute question, n'hésitez pas à nous contacter.\n\n"
    message += "Cordialement,\n"
    message += "L'équipe MEDD"
    
    return message

def generer_lien_whatsapp(telephone, message):
    """Génère un lien WhatsApp cliquable"""
    # Nettoyer le numéro de téléphone
    telephone_clean = ''.join(filter(str.isdigit, telephone))
    
    # S'assurer que le numéro commence par le code pays (supposons Congo +242)
    if not telephone_clean.startswith('242') and len(telephone_clean) == 9:
        telephone_clean = '242' + telephone_clean
    
    # Encoder le message pour l'URL
    message_encoded = urllib.parse.quote(message)
    
    # Créer le lien WhatsApp
    lien = f"https://wa.me/{telephone_clean}?text={message_encoded}"
    
    return lien

# ============================================================================
# PAGE RELANCES WHATSAPP
# ============================================================================

st.title("📱 Relances WhatsApp")

st.info("💡 **Cette page vous permet de générer des messages WhatsApp personnalisés pour relancer les participants avec des cotisations impayées.**")

# Récupérer les participants avec impayés
participants_impayees = get_participants_impayees()

if participants_impayees.empty:
    st.success("🎉 **Aucune cotisation impayée !** Tous les participants sont à jour.")
    st.stop()

# Afficher le nombre total de participants à relancer
st.metric(
    "👥 Participants à relancer", 
    len(participants_impayees),
    help="Nombre de participants avec des cotisations impayées et un numéro de téléphone"
)

st.divider()

# ============================================================================
# SECTION DE GÉNÉRATION DE MESSAGES
# ============================================================================

st.subheader("📝 Générer des messages de relance")

# Option pour sélectionner un ou plusieurs participants
mode_selection = st.radio(
    "Mode de sélection",
    ["Un participant", "Sélection multiple", "Tous les participants"],
    horizontal=True
)

if mode_selection == "Un participant":
    # Sélection unique
    participants_dict = {f"{row['nom']} {row['prenom']} ({row['montant_total']:,.0f} FCFA)".replace(',', ' '): row 
                        for _, row in participants_impayees.iterrows()}
    
    selected = st.selectbox(
        "Sélectionner un participant",
        options=list(participants_dict.keys())
    )
    
    if selected:
        participant = participants_dict[selected]
        
        # Afficher les détails
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Nom:** {participant['nom']} {participant['prenom']}")
            st.write(f"**Téléphone:** {participant['telephone']}")
            st.write(f"**Nombre d'impayées:** {int(participant['nb_impayees'])}")
        with col2:
            st.write(f"**Montant total:** {participant['montant_total']:,.0f} FCFA".replace(',', ' '))
        
        st.divider()
        
        # Récupérer les détails des cotisations impayées
        details = get_details_impayees(participant['id'])
        
        # Générer le message
        message = generer_message_whatsapp(
            participant['nom'],
            participant['prenom'],
            details,
            participant['montant_total']
        )
        
        st.subheader("📄 Message généré")
        st.text_area("Aperçu du message", message, height=300)
        
        # Bouton pour ouvrir WhatsApp
        lien_whatsapp = generer_lien_whatsapp(participant['telephone'], message)
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            st.link_button(
                "📱 Ouvrir dans WhatsApp",
                lien_whatsapp,
                type="primary",
                use_container_width=True
            )
        with col_btn2:
            if st.button("📋 Copier le message", use_container_width=True):
                st.code(message, language=None)
                st.success("Message affiché ci-dessus, vous pouvez le copier manuellement")
                
                # Enregistrer dans l'historique
                ajouter_historique(
                    'RELANCE',
                    'participants',
                    participant['id'],
                    f"Relance WhatsApp générée - {participant['nb_impayees']} cotisation(s) impayée(s)",
                    None,
                    f"Montant: {participant['montant_total']} FCFA"
                )

elif mode_selection == "Sélection multiple":
    # Sélection multiple avec checkboxes
    st.write("**Sélectionnez les participants à relancer:**")
    
    selected_participants = []
    
    for idx, row in participants_impayees.iterrows():
        col_check, col_info = st.columns([0.5, 9.5])
        
        with col_check:
            if st.checkbox("", key=f"check_{row['id']}"):
                selected_participants.append(row)
        
        with col_info:
            st.write(f"**{row['nom']} {row['prenom']}** - {row['telephone']} - {row['nb_impayees']} impayée(s) - {row['montant_total']:,.0f} FCFA".replace(',', ' '))
    
    if selected_participants:
        st.divider()
        st.write(f"**{len(selected_participants)} participant(s) sélectionné(s)**")
        
        if st.button("📱 Générer les messages pour la sélection", type="primary"):
            for participant in selected_participants:
                details = get_details_impayees(participant['id'])
                message = generer_message_whatsapp(
                    participant['nom'],
                    participant['prenom'],
                    details,
                    participant['montant_total']
                )
                lien_whatsapp = generer_lien_whatsapp(participant['telephone'], message)
                
                with st.expander(f"📱 {participant['nom']} {participant['prenom']}"):
                    st.text_area(f"Message", message, height=200, key=f"msg_{participant['id']}")
                    st.link_button(
                        "Ouvrir dans WhatsApp",
                        lien_whatsapp,
                        key=f"btn_{participant['id']}"
                    )
                    
                # Enregistrer dans l'historique
                ajouter_historique(
                    'RELANCE',
                    'participants',
                    participant['id'],
                    f"Relance WhatsApp générée - {participant['nb_impayees']} cotisation(s) impayée(s)",
                    None,
                    f"Montant: {participant['montant_total']} FCFA"
                )

else:  # Tous les participants
    st.warning(f"⚠️ Vous êtes sur le point de générer des messages pour **{len(participants_impayees)} participant(s)**")
    
    if st.button("📱 Générer tous les messages", type="primary"):
        for idx, participant in participants_impayees.iterrows():
            details = get_details_impayees(participant['id'])
            message = generer_message_whatsapp(
                participant['nom'],
                participant['prenom'],
                details,
                participant['montant_total']
            )
            lien_whatsapp = generer_lien_whatsapp(participant['telephone'], message)
            
            with st.expander(f"📱 {participant['nom']} {participant['prenom']} - {participant['montant_total']:,.0f} FCFA".replace(',', ' ')):
                col_msg, col_btn = st.columns([3, 1])
                
                with col_msg:
                    st.text_area(f"Message", message, height=150, key=f"msg_all_{participant['id']}")
                
                with col_btn:
                    st.link_button(
                        "Ouvrir WhatsApp",
                        lien_whatsapp,
                        key=f"btn_all_{participant['id']}",
                        use_container_width=True
                    )
            
            # Enregistrer dans l'historique
            ajouter_historique(
                'RELANCE',
                'participants',
                participant['id'],
                f"Relance WhatsApp générée - {participant['nb_impayees']} cotisation(s) impayée(s)",
                None,
                f"Montant: {participant['montant_total']} FCFA"
            )

st.divider()

# ============================================================================
# HISTORIQUE DES RELANCES
# ============================================================================

st.subheader("📋 Historique des relances récentes")

conn = sqlite3.connect(DB_NAME)
historique_df = pd.read_sql_query("""
    SELECT 
        h.date_action,
        p.nom,
        p.prenom,
        h.details,
        h.nouvelle_valeur
    FROM historique h
    LEFT JOIN participants p ON h.id_enregistrement = p.id
    WHERE h.type_action = 'RELANCE'
    ORDER BY h.date_action DESC
    LIMIT 20
""", conn)
conn.close()

if not historique_df.empty:
    st.dataframe(
        historique_df,
        column_config={
            "date_action": "Date",
            "nom": "Nom",
            "prenom": "Prénom",
            "details": "Détails",
            "nouvelle_valeur": "Montant"
        },
        hide_index=True,
        use_container_width=True
    )
else:
    st.info("Aucune relance enregistrée pour le moment")

# ============================================================================
# CONSEILS
# ============================================================================

st.divider()
st.subheader("💡 Conseils pour les relances")

col_conseil1, col_conseil2 = st.columns(2)

with col_conseil1:
    st.markdown("""
    **📱 Utilisation de WhatsApp:**
    - Cliquez sur "Ouvrir dans WhatsApp" pour envoyer directement
    - Le message s'ouvrira dans WhatsApp Web ou l'app mobile
    - Vous pouvez modifier le message avant l'envoi
    - Assurez-vous que le numéro est correct
    """)

with col_conseil2:
    st.markdown("""
    **✅ Bonnes pratiques:**
    - Relancez avec courtoisie et professionnalisme
    - Espacez les relances (1 fois par semaine max)
    - Proposez des solutions de paiement
    - Restez disponible pour répondre aux questions
    """)
