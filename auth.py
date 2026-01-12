"""
Module d'authentification pour l'application
"""

import streamlit as st
import hashlib
import json
import os

# Fichier pour stocker les utilisateurs
USERS_FILE = "users.json"

def hash_password(password):
    """Crée un hash SHA256 du mot de passe"""
    return hashlib.sha256(password.encode()).hexdigest()

def init_users_file():
    """Initialise le fichier utilisateurs avec un compte admin par défaut"""
    if not os.path.exists(USERS_FILE):
        default_users = {
            "admin": {
                "password": hash_password("admin123"),
                "nom": "Administrateur"
            }
        }
        with open(USERS_FILE, 'w') as f:
            json.dump(default_users, f, indent=4)

def load_users():
    """Charge les utilisateurs depuis le fichier"""
    init_users_file()
    with open(USERS_FILE, 'r') as f:
        return json.load(f)

def verify_credentials(username, password):
    """Vérifie les identifiants de l'utilisateur"""
    users = load_users()
    if username in users:
        password_hash = hash_password(password)
        if users[username]["password"] == password_hash:
            return True, users[username]["nom"]
    return False, None

def is_authenticated():
    """Vérifie si l'utilisateur est authentifié"""
    return st.session_state.get('authenticated', False)

def login_user(username, nom):
    """Connecte l'utilisateur"""
    st.session_state.authenticated = True
    st.session_state.username = username
    st.session_state.nom_utilisateur = nom

def logout_user():
    """Déconnecte l'utilisateur"""
    st.session_state.authenticated = False
    st.session_state.username = None
    st.session_state.nom_utilisateur = None

def show_login_page():
    """Affiche la page de connexion"""
    st.markdown("""
        <style>
        .login-container {
            max-width: 400px;
            margin: 100px auto;
            padding: 2rem;
            background-color: #f0f2f6;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("# 🔐 Connexion")
        st.markdown("### Gestion du Terrain MEDD")
        st.divider()
        
        with st.form("login_form"):
            username = st.text_input("👤 Nom d'utilisateur", key="login_username")
            password = st.text_input("🔑 Mot de passe", type="password", key="login_password")
            
            submit = st.form_submit_button("Se connecter", use_container_width=True, type="primary")
            
            if submit:
                if username and password:
                    success, nom = verify_credentials(username, password)
                    if success:
                        login_user(username, nom)
                        st.success(f"Bienvenue {nom} !")
                        st.rerun()
                    else:
                        st.error("❌ Identifiants incorrects")
                else:
                    st.warning("⚠️ Veuillez remplir tous les champs")
        
        st.divider()
        st.info("💡 **Compte par défaut :**\nUtilisateur : `admin`\nMot de passe : `admin123`")
        st.caption("⚠️ Pensez à changer le mot de passe par défaut après la première connexion")

def require_authentication():
    """Vérifie l'authentification et affiche la page de connexion si nécessaire"""
    if not is_authenticated():
        show_login_page()
        st.stop()

def show_logout_button():
    """Affiche un bouton de déconnexion dans la sidebar"""
    if is_authenticated():
        st.sidebar.divider()
        st.sidebar.write(f"👤 Connecté : **{st.session_state.nom_utilisateur}**")
        if st.sidebar.button("🚪 Se déconnecter", use_container_width=True):
            logout_user()
            st.rerun()
