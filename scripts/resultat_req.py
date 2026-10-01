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
# paramètres de test
nb_lig_erp = 825 
nb_lig_liaison = 825 
nb_lig_web = 1428
nb_lig_web_db = 714

con = None


db_path_duckdb = sys.argv[1]

#-----------------------------
#  DEDOUBLONNAGE TABLE DUCKDB
#-----------------------------
print(f"--- ANALYSE  TABLES DUCKDB  ---\n")

try:
    con = duckdb.connect(db_path_duckdb)

    count_1 = con.execute(f'SELECT COUNT(*) FROM fichier_erp ').fetchone()[0]
    count_2 = con.execute(f'SELECT COUNT(*) FROM fichier_liaison ').fetchone()[0]
    count_3 = con.execute(f'SELECT COUNT(*) FROM fichier_web ').fetchone()[0]

    print(f"Table : fichier_erp  nombre de lignes : {count_1}")
    print(f"Table : fichier_liaison nombre de lignes : {count_2}")
    print(f"Table : fichier_web  nombre de lignes : {count_3}")





    # ---------------------------------------------------------
    #  Vérifier s'il y a des doublons et les compter
    # ---------------------------------------------------------
    resultat_doublons = con.execute("""
        SELECT 
            COUNT(*) AS lignes_totales,
            COUNT(DISTINCT product_id) AS prod_uniques,
            COUNT(*) - COUNT(DISTINCT product_id) AS nb_doublons
        FROM fichier_erp
        WHERE product_id IS NOT NULL;
    """).fetchone()
    lignes_totales, prod_uniques, nb_doublons = resultat_doublons
    print ("Dédoublonnage fichier_erp")
    print(f"Lignes totales : {lignes_totales}")
    print(f"Produits uniques : {prod_uniques}")
    print(f"Nombre de doublons détectés : {nb_doublons}")
    if nb_doublons > 0:
        print("\nSuppression des doublons en cours...")
        
        con.execute("""
            CREATE OR REPLACE TABLE fichier_erp AS 
            SELECT * EXCLUDE (row_num)
            FROM (
                SELECT *, 
                       ROW_NUMBER() OVER (
                           PARTITION BY product_id 
                           ORDER BY product_id -- Tu peux ajouter un critère (ex: date_modif DESC)
                       ) AS row_num
                FROM fichier_erp
                WHERE product_id IS NOT NULL
            )
            WHERE row_num = 1;
        """)
        # ---------------------------------------------------------
        # Vérification après nettoyage
        # ---------------------------------------------------------
        lignes_apres = con.execute("SELECT COUNT(*) FROM fichier_erp").fetchone()[0]
        print(f"Nettoyage terminé ! Lignes restantes : {lignes_apres}")
        if nb_lig_erp == lignes_apres:
            print(f"--- Test vérification dédoublonnage fichier_erp :{nb_lig_erp} dans la base : {lignes_apres}  --- ")
        else:
            print(f"--- Erreur test vérification dédoublonnage fichier_erp :{nb_lig_erp} dans la base : {lignes_apres}  --- ")

    else:
        print("Aucun doublon trouvé sur la colonne product_id fichier_erp.")
        if nb_lig_erp == lignes_totales:
            print(f"--- Test vérification dédoublonnage fichier_erp :{nb_lig_erp} dans la base : {lignes_totales}  --- ")
        else:
            print(f"--- Erreur test vérification dédoublonnage fichier_erp :{nb_lig_erp} dans la base : {lignes_totales}  --- ")
    # ----------------------------------------------------------------------
    #  Détection et comptage des doublons sur le couple (id_web, product_id)
    # ----------------------------------------------------------------------
    stats = con.execute("""
        SELECT 
            COUNT(*) AS total_lignes,
            COUNT(DISTINCT (id_web, product_id)) AS couples_uniques,
            COUNT(*) - COUNT(DISTINCT (id_web, product_id)) AS nb_doublons
        FROM fichier_liaison;


    """).fetchone()

    total_lignes, couples_uniques, nb_doublons = stats
    print ("\nDédoublonnage fichier_liaison")
    print(f"Total des lignes : {total_lignes}")
    print(f"Couples (id_web, product_id) uniques : {couples_uniques}")
    print(f"Doublons stricts détectés : {nb_doublons}")

    # ----------------------------------------------------------------
    # Dédoublonnage sur la combinaison des 2 colonnes fichier_liaison
    # ---------------------------------------------------------------
    if nb_doublons > 0:
        print("Suppression des doublons en cours...")
        
        con.execute("""
            CREATE OR REPLACE TABLE fichier_liaison AS 
            SELECT * EXCLUDE (row_num)
            FROM (
                SELECT *, 
                       ROW_NUMBER() OVER (
                           PARTITION BY id_web, product_id 
                           ORDER BY id_web, product_id -- Ajoute un ORDER BY (ex: date DESC) si besoin
                       ) AS row_num
                FROM fichier_liaison
                WHERE id_web IS NOT NULL 
                  AND product_id IS NOT NULL
            )
            WHERE row_num = 1;
        """)
        
        # ---------------------------------------------------------
        #  Vérification finale
        # ---------------------------------------------------------
        lignes_apres = con.execute("SELECT COUNT(*) FROM fichier_liaison").fetchone()[0]
        print(f"Nettoyage terminé ! Lignes conservées : {lignes_apres}")
        if nb_lig_liaison == lignes_apres:
            print(f"--- Test vérification dédoublonnage fichier_erp :{nb_lig_erp} dans la base : {lignes_apres}  --- ")
        else:
            print(f"--- Erreur test vérification dédoublonnage fichier_erp :{nb_lig_erp} dans la base : {lignes_apres}  --- ")

    else:
        print("Aucun doublon trouvé sur la combinaison (id_web, product_id) fichier liaison .")
        if nb_lig_liaison == total_lignes:
            print(f"--- Test vérification dédoublonnage fichier_liaison :{nb_lig_erp} dans la base : {total_lignes}  --- ")
        else:
            print(f"--- Erreur test vérification dédoublonnage fichier_erp :{nb_lig_erp} dans la base : {total_lignes}  --- ")


    print ("\n Nettoyage fichier_web")
    con.execute("""DELETE FROM fichier_web WHERE id_web IS NULL OR id_web = '' ;""")
    lignes_apres = con.execute("SELECT COUNT(*) FROM fichier_web").fetchone()[0]
    if nb_lig_web == lignes_apres:
        print(f"--- Test vérification nettoyage fichier_web :{nb_lig_web} dans la base : {lignes_apres}  --- ")
    else:
        print(f"--- Erreur test vérification nettoyage fichier_web :{nb_lig_web} dans la base : {lignes_apres}  --- ")


    print ("\n Dédoublonnage fichier_web")
    con.execute("""DELETE FROM fichier_web WHERE post_type != 'product' ;""")
    lignes_apres = con.execute("SELECT COUNT(*) FROM fichier_web").fetchone()[0]
    if nb_lig_web_db == lignes_apres:
        print(f"--- Test vérification dédoublonnage fichier_web :{nb_lig_web_db} dans la base : {lignes_apres}  --- ")
    else:
        print(f"--- Erreur test vérification dédoublonnage fichier_web :{nb_lig_web_db} dans la base : {lignes_apres}  --- ")

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




print(f"\n --- GENERATION DU RAPPORT  ---\n")



con =None

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

    df_ca.to_excel("rapport_chiffre_affaires_produit.xlsx", index=False, engine="openpyxl")

    print(f"Fichier Excel CA généré : rapport_chiffre_affaires_produit.xlsx ")


    if file_fusion !=  len(df_ca) :
        print (f"---> Problème entre fichier fusionné calculé :{len(df_ca)} et attendu : {file_fusion} --- ")
    else :
        print (f"--- Test vérification nb fichier fusionné réussi calculé :{len(df_ca)} et attendu : {file_fusion} --- ")


    ca_total = df_ca['chiffre_affaires'].sum()

    if ca_total_attendu != ca_total :
        print(f"---> Problème entre CA attendu et CA calculé   ")
    else :
        print("\n--- Test vérification CA réussi --- ")


    print(f"Chiffre d'Affaires Total  : {ca_total:,.2f} € /  Chiffre d'Affaires  attendu : {ca_total_attendu:,.2f} €")



    # Sécuriser la conversion de ca_total en float
    ca_total_valeur = float(ca_total)

    df_export = pd.DataFrame({'chiffre_affaires_total': [ca_total_valeur]})

    df_export.to_excel("chiffre_affaires_total.xlsx", index=False, engine="openpyxl")

    print (df_export)

    print ("Fichier Excel généré : chiffre_affaires_total.xlsx ")


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







