import duckdb
import pandas as pd
import numpy as np
from scipy import stats
import os
import sys
from pathlib import Path
import json
import atexit


try:
    from kestra import Kestra
    HAS_KESTRA_LIB = True
except ImportError:
    HAS_KESTRA_LIB = False


# pile de logs
logs = []
_original_print = print

def print(*args, **kwargs):
    """Surcharge de print pour capturer la sortie textuelle."""
    msg = " ".join(str(a) for a in args)
    logs.append(msg)
    _original_print(*args, **kwargs)

def export_kestra_outputs():
    """Envoie les logs accumulés vers Kestra à la fin de l'exécution."""
    full_logs = "\n".join(logs)
    if HAS_KESTRA_LIB:
        Kestra.outputs({"pipeline_logs": full_logs})
    else:
        # Syntaxe standard de sortie stdout reconnue par Kestra
        _original_print(f'::{{\"outputs\": {json.dumps({"pipeline_logs": full_logs})}}}::')

# Enregistrement de la fonction d'envoi à la fermeture du script
atexit.register(export_kestra_outputs)




# paramètres des tests

ca_total_attendu = 70568.60
nb_vin_mil =30
file_fusion =714

con = None


db_path_duckdb = sys.argv[1]


print(f"--- GENERATION DU RAPPORT  ---\n")

print(f"Fichiers présents : {db_path_duckdb}")

con =None

'''
# Vérification si les tables sont présentes et ont le bon nom
try:
    con = duckdb.connect(db_path_duckdb)

    query_ca = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'main';
    """
    df_table= con.execute(query_ca).df()
    print("Liste des tables duckdb dans resultat_req :")
    print(df_table)

    con.close()
except AssertionError as e:
    print (f"Erreur echec du script: {e}", file=sys.stderr)
    sys.exit(1)   
except Exception as e :
    print (f"Erreur echec du script: {e}", file=sys.stderr)
    sys.exit(1)    
finally :
    if con is not None :
        con.close()
        print("Close connexion SQL")
'''

try: 
    con = duckdb.connect(db_path_duckdb)
    
    # =========================
    # Génération du Rapport
     # =========================
    query_ca = """
    SELECT 
        e.product_id,
        l.id_web,
        w.post_title AS nom_produit,
        e.price AS prix_unitaire,
        COALESCE(w.total_sales, 0) AS ventes_totales,
        ROUND(e.price * COALESCE(w.total_sales, 0), 2) AS chiffre_affaires,
        e.stock_quantity AS stock
    FROM fichier_erp e
    INNER JOIN fichier_liaison l ON e.product_id = l.product_id
    INNER JOIN fichier_web w ON l.id_web = w.id_web
    ORDER BY chiffre_affaires DESC;
    """
    
    df_ca = con.execute(query_ca).df()

    df_ca.to_excel("rapport_chiffre_affaires.xlsx", index=False, engine="openpyxl")

    print(f"Fichier Excel CA généré : rapport_chiffre_affaires.xlsx ")
    ca_total = df_ca['chiffre_affaires'].sum()

    if ca_total_attendu != ca_total :
        print(f"---> Problème entre CA attendu et CA calculé   ")
    else :
        print("\n--- Test vérification CA réussi --- ")


    print(f"Chiffre d'Affaires Total  : {ca_total:,.2f} € /  Chiffre d'Affaires  attendu : {ca_total_attendu:,.2f} €")



    if file_fusion !=  len(df_ca) :
        print (f"---> Problème entre fichier fusionné calculé :{len(df_ca)} et attendu : {file_fusion}  ")
    else :
        print("\n--- Test vérification nb fichier fusionné réussi --- ")
 



    # -------------------------------------------------------------
    # CALCUL DU Z-SCORE STATISTIQUE SUR L'ENSEMBLE DES PRIX
    # -------------------------------------------------------------
    # Z-Score = (prix - moyenne_prix) / ecart_type_prix
    cte_zscore = """
        WITH dataset AS (
            SELECT 
                e.product_id,
                l.id_web,
                w.post_title AS nom_produit,
                e.price AS prix_unitaire,
                COALESCE(w.total_sales, 0) AS ventes_totales,
                ROUND(e.price * COALESCE(w.total_sales, 0), 2) AS chiffre_affaires,
                e.stock_quantity AS stock,
                -- Calcul de la moyenne et de l'écart-type sur le périmètre
                AVG(e.price) OVER () AS avg_price,
                STDDEV(e.price) OVER () AS std_price
            FROM fichier_erp e
            INNER JOIN fichier_liaison l ON e.product_id = l.product_id
            INNER JOIN fichier_web w ON l.id_web = w.id_web
        )
        SELECT 
            product_id,
            id_web,
            nom_produit,
            prix_unitaire,
            ROUND((prix_unitaire - avg_price) / std_price, 4) AS z_score,
            ventes_totales,
            chiffre_affaires,
            stock
        FROM dataset
    """
    # -------------------------------------------------------------
    # EXTRACTION : Vins Premium (Z-Score > 2) (.csv)
    # -------------------------------------------------------------
    query_premium = f"""
        {cte_zscore}
        WHERE (prix_unitaire - avg_price) / std_price > 2
        ORDER BY z_score DESC;
    """
    df_premium = con.execute(query_premium).df()    
    df_premium.to_csv("vins_premium.csv", index=False, encoding="utf-8")

    print(f"\nFichier CSV vins premium (Z-Score > 2) généré : vins_premium.csv ")  
    print(f"Nombre de vins millésimes : {len(df_premium)}") 
    print(f"Nombre de vins millésimes attendus: {nb_vin_mil}") 
    if nb_vin_mil != len(df_premium) :
        print("---> Problème entre vins millésimes attendu et vins millésimes calculé ")
        print(f"Vins millésimes calculé : {len(df_premium)} et vins millésimes attendu {nb_vin_mil}")
    else :
        print("--- Test nombre vins millésimes réussi --- \n")

    # -------------------------------------------------------------
    #  EXTRACTION : Vins Ordinaires (Z-Score <= 2) (.csv)
    # -------------------------------------------------------------
    query_ordinaires = f"""
        {cte_zscore}
        WHERE (prix_unitaire - avg_price) / std_price <= 2
        ORDER BY z_score DESC;
    """
    df_ordinaires = con.execute(query_ordinaires).df()
    df_ordinaires.to_csv("vins_ordinaires.csv", index=False, encoding="utf-8")
    

    print(f"\nFichier CSV Vins Ordinaires (Z-Score <= 2) généré  : vins_ordinaires.csv")

    
    
except AssertionError as e:
    print (f"Erreur echec du script: {e}", file=sys.stderr)
    sys.exit(1)   
except Exception as e :
    print (f"Erreur echec du script: {e}", file=sys.stderr)
    sys.exit(1)    
finally :
    if con is not None :
        con.close()
        #print("Close connexion SQL")
