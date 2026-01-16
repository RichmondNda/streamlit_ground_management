"""
Module pour générer des rapports PDF pour les participants
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas
import io
from datetime import datetime
import sqlite3
from database import DB_NAME
from constants import MOIS_NOMS, PRIX_TERRAIN, COTISATION_PAR_TERRAIN
import matplotlib
matplotlib.use('Agg')  # Backend non-interactif pour génération de graphiques
import matplotlib.pyplot as plt
import numpy as np

def generer_rapport_participant(participant_id):
    """
    Génère un rapport PDF complet pour un participant
    
    Returns:
        BytesIO object contenant le PDF
    """
    # Récupérer les informations du participant
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT nom, prenom, nombre_terrains, telephone, email 
        FROM participants WHERE id = ?
    """, (participant_id,))
    
    participant = cursor.fetchone()
    if not participant:
        conn.close()
        return None
    
    nom, prenom, nb_terrains, telephone, email = participant
    
    # Récupérer toutes les cotisations
    cursor.execute("""
        SELECT annee, mois, montant, paye, date_paiement, numero_terrain
        FROM cotisations 
        WHERE participant_id = ?
        ORDER BY annee, mois, numero_terrain
    """, (participant_id,))
    
    cotisations = cursor.fetchall()
    conn.close()
    
    # Créer le PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, 
                           leftMargin=2*cm, rightMargin=2*cm,
                           topMargin=2*cm, bottomMargin=2*cm)
    
    # Styles
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#2F5496'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#4472C4'),
        spaceAfter=12,
        spaceBefore=12
    )
    
    normal_style = styles['Normal']
    
    # Contenu du document
    story = []
    
    # Titre
    story.append(Paragraph("RAPPORT DE COTISATIONS", title_style))
    story.append(Paragraph(f"Gestion MEDD - {datetime.now().strftime('%d/%m/%Y')}", 
                          ParagraphStyle('Date', parent=normal_style, alignment=TA_CENTER, textColor=colors.grey)))
    story.append(Spacer(1, 1*cm))
    
    # Informations du participant
    story.append(Paragraph("INFORMATIONS DU PARTICIPANT", heading_style))
    
    info_data = [
        ['Nom complet:', f"{nom} {prenom}"],
        ['Nombre de terrains:', str(nb_terrains)],
        ['Téléphone:', telephone or 'Non renseigné'],
        ['Email:', email or 'Non renseigné'],
        ['Coût total terrains:', f"{nb_terrains * PRIX_TERRAIN:,.0f} FCFA".replace(',', ' ')]
    ]
    
    info_table = Table(info_data, colWidths=[6*cm, 10*cm])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#E7E6E6')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    
    story.append(info_table)
    story.append(Spacer(1, 1*cm))
    
    # Statistiques globales
    if cotisations:
        # Le montant attendu est la somme de TOUS les montants de cotisations (payées ou non)
        total_attendu = sum(c[2] for c in cotisations)
        # Le montant payé est la somme des montants des cotisations marquées comme payées
        total_paye = sum(c[2] for c in cotisations if c[3] == 1)
        nb_payees = sum(1 for c in cotisations if c[3] == 1)
        taux_paiement = (nb_payees / len(cotisations) * 100) if cotisations else 0
        
        story.append(Paragraph("RÉSUMÉ FINANCIER", heading_style))
        
        stats_data = [
            ['Nombre total de cotisations:', str(len(cotisations))],
            ['Cotisations payées:', f"{nb_payees} ({taux_paiement:.1f}%)"],
            ['Cotisations impayées:', str(len(cotisations) - nb_payees)],
            ['Montant attendu:', f"{total_attendu:,.0f} FCFA".replace(',', ' ')],
            ['Montant encaissé:', f"{total_paye:,.0f} FCFA".replace(',', ' ')],
            ['Reste à payer:', f"{total_attendu - total_paye:,.0f} FCFA".replace(',', ' ')]
        ]
        
        stats_table = Table(stats_data, colWidths=[8*cm, 8*cm])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#D9E2F3')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (-1, 4), 'Helvetica'),
            ('FONTNAME', (1, 5), (1, 5), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('BACKGROUND', (0, 5), (-1, 5), colors.HexColor('#FFF2CC')),
        ]))
        
        story.append(stats_table)
        story.append(Spacer(1, 0.5*cm))
        
        # ====================================================================
        # AJOUTER DES GRAPHIQUES
        # ====================================================================
        
        # 1. Camembert du statut des cotisations
        fig1, ax1 = plt.subplots(figsize=(6, 4))
        sizes = [nb_payees, len(cotisations) - nb_payees]
        labels = ['Payées', 'Impayées']
        colors_pie = ['#28a745', '#dc3545']
        explode = (0.05, 0)  # Mettre en relief la première part
        
        ax1.pie(sizes, explode=explode, labels=labels, colors=colors_pie,
                autopct='%1.1f%%', startangle=90, textprops={'fontsize': 11})
        ax1.axis('equal')
        plt.title('Répartition des cotisations', fontsize=12, fontweight='bold')
        
        # Sauvegarder le graphique dans un buffer
        img_buffer1 = io.BytesIO()
        plt.savefig(img_buffer1, format='png', dpi=150, bbox_inches='tight')
        img_buffer1.seek(0)
        plt.close()
        
        # Ajouter l'image au PDF
        img1 = Image(img_buffer1, width=10*cm, height=6.5*cm)
        story.append(img1)
        story.append(Spacer(1, 0.5*cm))
        
        # 2. Graphique en barres par terrain (si applicable)
        cotis_par_terrain = {}
        for cotis in cotisations:
            terrain_num = cotis[5]  # numero_terrain
            if terrain_num:
                if terrain_num not in cotis_par_terrain:
                    cotis_par_terrain[terrain_num] = {'total': 0, 'paye': 0}
                cotis_par_terrain[terrain_num]['total'] += cotis[2]
                if cotis[3] == 1:
                    cotis_par_terrain[terrain_num]['paye'] += cotis[2]
        
        if cotis_par_terrain:
            fig2, ax2 = plt.subplots(figsize=(10, 4))
            
            terrains = sorted(cotis_par_terrain.keys())
            montants_payes = [cotis_par_terrain[t]['paye'] for t in terrains]
            montants_impayed = [cotis_par_terrain[t]['total'] - cotis_par_terrain[t]['paye'] for t in terrains]
            
            x = np.arange(len(terrains))
            width = 0.6
            
            ax2.bar(x, montants_payes, width, label='Payé', color='#28a745')
            ax2.bar(x, montants_impayed, width, bottom=montants_payes, 
                   label='Impayé', color='#dc3545')
            
            ax2.set_xlabel('Terrain', fontsize=10)
            ax2.set_ylabel('Montant (FCFA)', fontsize=10)
            ax2.set_title('Cotisations par terrain', fontsize=12, fontweight='bold')
            ax2.set_xticks(x)
            ax2.set_xticklabels([f'n°{t}' for t in terrains])
            ax2.legend()
            ax2.grid(axis='y', alpha=0.3)
            
            # Sauvegarder le graphique
            img_buffer2 = io.BytesIO()
            plt.savefig(img_buffer2, format='png', dpi=150, bbox_inches='tight')
            img_buffer2.seek(0)
            plt.close()
            
            # Ajouter l'image au PDF
            img2 = Image(img_buffer2, width=14*cm, height=6*cm)
            story.append(img2)
            story.append(Spacer(1, 0.5*cm))
        
        story.append(Spacer(1, 0.5*cm))
    
    # Détail des cotisations par année
    if cotisations:
        story.append(Paragraph("DÉTAIL DES COTISATIONS", heading_style))
        
        # Grouper par année
        cotis_par_annee = {}
        for cotis in cotisations:
            annee = cotis[0]
            if annee not in cotis_par_annee:
                cotis_par_annee[annee] = []
            cotis_par_annee[annee].append(cotis)
        
        for annee in sorted(cotis_par_annee.keys(), reverse=True):
            story.append(Paragraph(f"<b>Année {annee}</b>", normal_style))
            story.append(Spacer(1, 0.3*cm))
            
            # En-tête du tableau
            cotis_data = [['Mois', 'Terrain', 'Montant', 'Statut', 'Date paiement']]
            
            for cotis in sorted(cotis_par_annee[annee], key=lambda x: (x[1], x[5] or 0)):
                annee_c, mois, montant, paye, date_paiement, numero_terrain = cotis
                mois_nom = MOIS_NOMS[mois - 1]
                terrain_str = f"n°{numero_terrain}" if numero_terrain else "Tous"
                statut = "✓ Payée" if paye else "✗ Impayée"
                date_str = date_paiement if date_paiement else "-"
                
                cotis_data.append([
                    mois_nom,
                    terrain_str,
                    f"{montant:,.0f}".replace(',', ' '),
                    statut,
                    date_str
                ])
            
            cotis_table = Table(cotis_data, colWidths=[3*cm, 2*cm, 3*cm, 3*cm, 3*cm])
            cotis_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4472C4')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 1), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            ]))
            
            # Colorer les lignes selon le statut
            for i in range(1, len(cotis_data)):
                if "Payée" in cotis_data[i][3]:
                    cotis_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, i), (-1, i), colors.HexColor('#C6E0B4'))
                    ]))
                else:
                    cotis_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, i), (-1, i), colors.HexColor('#F8D7DA'))
                    ]))
            
            story.append(cotis_table)
            story.append(Spacer(1, 0.8*cm))
    else:
        story.append(Paragraph("Aucune cotisation enregistrée pour ce participant.", normal_style))
    
    # Footer
    story.append(Spacer(1, 2*cm))
    story.append(Paragraph("_______________________________________________", 
                          ParagraphStyle('Line', parent=normal_style, alignment=TA_CENTER)))
    story.append(Paragraph(f"Document généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}", 
                          ParagraphStyle('Footer', parent=normal_style, alignment=TA_CENTER, 
                                       fontSize=8, textColor=colors.grey)))
    story.append(Paragraph("Gestion des cotisations MEDD", 
                          ParagraphStyle('Footer2', parent=normal_style, alignment=TA_CENTER, 
                                       fontSize=8, textColor=colors.grey)))
    
    # Générer le PDF
    doc.build(story)
    buffer.seek(0)
    
    return buffer
