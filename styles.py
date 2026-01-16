"""
Styles CSS globaux pour l'application
"""

GLOBAL_STYLES = """
<style>
    /* ===== COULEURS PRINCIPALES ===== */
    :root {
        --primary-color: #fc6b03;
        --primary-hover: #e35f02;
        --background-light: #fafafa;
        --border-light: #e0e0e0;
    }
    
    /* ===== TYPOGRAPHIE ===== */
    h1 {
        color: #fc6b03;
        font-size: 2.5rem !important;
        font-weight: 700 !important;
        padding-bottom: 1rem;
        border-bottom: 3px solid #fc6b03;
        margin-bottom: 2rem;
    }
    
    h2, h3 {
        color: #fc6b03;
        font-weight: 600 !important;
        margin-top: 1.5rem !important;
    }
    
    /* ===== CONTENEURS ET CARTES ===== */
    .stExpander {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* ===== BOUTONS ===== */
    .stButton > button[kind="primary"] {
        background-color: #fc6b03;
        border-color: #fc6b03;
        color: white;
        font-weight: 600;
        border-radius: 8px;
        padding: 0.5rem 1rem;
    }
    
    .stButton > button[kind="primary"]:hover {
        background-color: #e35f02;
        border-color: #e35f02;
    }
    
    .stButton > button {
        border-radius: 8px;
    }
    
    /* ===== MÉTRIQUES ===== */
    [data-testid="stMetricValue"] {
        color: #fc6b03;
        font-size: 1.8rem !important;
        font-weight: 700 !important;
    }
    
    [data-testid="stMetricLabel"] {
        font-weight: 600;
    }
    
    /* ===== INPUTS ET FORMULAIRES ===== */
    .stTextInput > div > div > input,
    .stSelectbox > div > div > div,
    .stNumberInput > div > div > input {
        border-radius: 8px;
        border-color: #e0e0e0;
    }
    
    .stTextInput > div > div > input:focus,
    .stSelectbox > div > div > div:focus-within,
    .stNumberInput > div > div > input:focus {
        border-color: #fc6b03;
        box-shadow: 0 0 0 1px #fc6b03;
    }
    
    /* ===== MESSAGES ===== */
    .stSuccess {
        background-color: #e8f5e9;
        color: #2e7d32;
        border-left: 4px solid #4caf50;
        border-radius: 8px;
        padding: 1rem;
    }
    
    .stError {
        background-color: #ffebee;
        color: #c62828;
        border-left: 4px solid #f44336;
        border-radius: 8px;
        padding: 1rem;
    }
    
    .stWarning {
        background-color: #fff3e0;
        color: #e65100;
        border-left: 4px solid #ff9800;
        border-radius: 8px;
        padding: 1rem;
    }
    
    .stInfo {
        background-color: #e3f2fd;
        color: #0d47a1;
        border-left: 4px solid #2196f3;
        border-radius: 8px;
        padding: 1rem;
    }
    
    /* ===== DIVIDERS ===== */
    hr {
        border-color: #fc6b03;
        margin: 2rem 0;
        opacity: 0.3;
    }
    
    /* ===== SIDEBAR ===== */
    .stSidebar {
        background-color: #fafafa;
    }
    
    .stSidebar .stInfo {
        background-color: #fff3e0;
        border-left: 4px solid #fc6b03;
        border-radius: 8px;
    }
    
    /* ===== TABLEAUX ===== */
    .dataframe {
        border-radius: 8px;
        overflow: hidden;
    }
    
    .dataframe thead tr th {
        background-color: #fc6b03 !important;
        color: white !important;
        font-weight: 600 !important;
    }
    
    .dataframe tbody tr:hover {
        background-color: #fff3e0 !important;
    }
    
    /* ===== TABS ===== */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0;
        padding: 10px 20px;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #fc6b03;
        color: white;
    }
    
    /* ===== ANIMATIONS ===== */
    /* Animations désactivées */
    
    /* ===== SCROLLBAR ===== */
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #fc6b03;
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #e35f02;
    }
    
    /* ===== RESPONSIVE ===== */
    @media (max-width: 768px) {
        h1 {
            font-size: 2rem !important;
        }
        
        .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
        }
    }
</style>
"""
