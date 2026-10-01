
import os
import sys

# Désactive l'import de 'bottleneck' local avant de charger Pandas
sys.modules['bottleneck'] = None

import warnings
import duckdb
import pandas as pd
import numpy as np
from scipy import stats

from pathlib import Path
import json
import atexit


# paramètres de test
nb_lig_erp = 825 
nb_lig_liaison = 825 
nb_lig_web = 1428
nb_lig_web_db = 714

warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

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


# Récupération du nom du fichier
file_name = sys.argv[1]
file_path = Path(file_name)

output_csv = file_path.stem.lower() + ".csv"

print (f"--- DEBUT DU PIPELINE TRAITEMENT FICHIER : {file_name} ---\n")
print (f"Fichier CSV de sortie  : {output_csv}")




try:
    df_xls = pd.read_excel(file_path)
    print(f"Succès ! {len(df_xls)} lignes chargées pour {file_name}.")
except Exception as e:
    print(f"Erreur critique lors de la lecture : {e}")
    sys.exit(1)


#  Renommage sécurisé de 'sku' en 'id_web' si présent
if 'sku' in df_xls.columns:
    df_xls = df_xls.rename(columns={'sku': 'id_web'})


#  Détection dynamique des colonnes cibles présentes dans le fichier
cols_a_nettoyer = [col for col in ['product_id', 'id_web'] if col in df_xls.columns]

#  Suppression des NaN uniquement sur les colonnes présentes
if cols_a_nettoyer:
    df_xls = df_xls.dropna(subset=cols_a_nettoyer)
    print(f" {file_name} -> NaN supprimés sur : {cols_a_nettoyer}")


#  FILTRAGE PAR POST_TYPE (si la colonne existe)
if 'post_type' in df_xls.columns:
    nb_avant = len(df_xls)
    # On conserve uniquement les lignes où post_type vaut "product"
    df_xls = df_xls[df_xls['post_type'] == 'product']
    nb_apres = len(df_xls)
    print(f"{file_name} -> Filtre post_type='product' : {nb_avant - nb_apres} lignes écartées ({nb_apres} conservées).")


# DÉTECTION ET SUPPRESSION DES DOUBLONS RESTANTS
cols_cles = [col for col in ['product_id', 'id_web'] if col in df_xls.columns]

if cols_cles:
    nb_doublons = df_xls.duplicated(subset=cols_cles).sum()
    
    if nb_doublons > 0:
        print(f"{file_name} {nb_doublons} doublon(s) trouvé(s) sur {cols_cles}.")
        df_xls = df_xls.drop_duplicates(subset=cols_cles, keep='first')
        print(f" {file_name} -> Doublons supprimés. Lignes restantes : {len(df_xls)}")
    else:
        print(f"{file_name} Aucun doublon trouvé sur {cols_cles}.")

# Sauvegarde en CSV
df_xls.to_csv(output_csv, index=False)
print (f"\n--- FIN DU PIPELINE TRAITEMENT FICHIER : {file_name} ---")

