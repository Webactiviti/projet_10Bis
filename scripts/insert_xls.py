
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


# Récupération du nom des fichiers
file_name_xls_1 = sys.argv[1]
file_name_xls_2 = sys.argv[2]
file_name_xls_3 = sys.argv[3]


print ("--- DEBUT DU PIPELINE TRAITEMENT FICHIER XLS ---\n")


db_path_duckdb ="fichiersql.duckdb"

#---------------------------------------
# Lecture 1er fichier XLS
#---------------------------------------
file_path_1 = Path(file_name_xls_1)
table_name_1 = file_path_1.stem.lower() 
try:

    df_xls_1 = pd.read_excel(file_path_1)
    
    #  Renommage sécurisé de 'sku' en 'id_web' si présent
    if 'sku' in df_xls_1.columns:
        df_xls_1 = df_xls_1.rename(columns={'sku': 'id_web'})

    print(f"Succès fichier N°1 ! {len(df_xls_1)} lignes chargées pour {file_name_xls_1}.")
except Exception as e:
    print(f"Erreur critique fichier N°1 lors de la lecture : {e}")
    sys.exit(1)

#---------------------------------------
# Lecture 2 ème fichier XLS
#---------------------------------------
file_path_2 = Path(file_name_xls_2)
table_name_2 = file_path_2.stem.lower() 
try:
    df_xls_2 = pd.read_excel(file_path_2)
    #  Renommage sécurisé de 'sku' en 'id_web' si présent
    if 'sku' in df_xls_2.columns:
        df_xls_2 = df_xls_2.rename(columns={'sku': 'id_web'})
 
    print(f"Succès fichier N°2 ! {len(df_xls_2)} lignes chargées pour {file_name_xls_2}.")
except Exception as e:
    print(f"Erreur critique fichier N°2 lors de la lecture : {e}")
    sys.exit(1)

#---------------------------------------
# Lecture 3 ème fichier XLS
#---------------------------------------
file_path_3 = Path(file_name_xls_3)
table_name_3 = file_path_3.stem.lower() 
try:
    df_xls_3 = pd.read_excel(file_path_3)
    #  Renommage sécurisé de 'sku' en 'id_web' si présent
    if 'sku' in df_xls_3.columns:
        df_xls_3 = df_xls_3.rename(columns={'sku': 'id_web'})
 
    print(f"Succès fichier N°3 ! {len(df_xls_3)} lignes chargées pour {file_name_xls_3}.")
except Exception as e:
    print(f"Erreur critique fichier N°3 lors de la lecture : {e}")
    sys.exit(1)


# -----------------------------------------------
# insertion dans la base duckDB des fichiers CSV
# -----------------------------------------------

con = None
try: 
    con = duckdb.connect(db_path_duckdb)
    # Enregistrement des DataFrames dans DuckDB

    con.register('xls1_temp', df_xls_1)
    con.execute (f"CREATE or REPLACE TABLE {table_name_1} as select * from xls1_temp" )
    
    con.register('xls2_temp', df_xls_2)
    con.execute (f"CREATE or REPLACE TABLE {table_name_2} as select * from xls2_temp" )
    
    con.register('xls3_temp', df_xls_3)
    con.execute (f"CREATE or REPLACE TABLE {table_name_3} as select * from xls3_temp " )

    con.execute ("CHECKPOINT")
    #print ("\nInsertion des fichiers terminé")
    

    count_1 = con.execute(f'SELECT COUNT(*) FROM {table_name_1} ').fetchone()[0]
    count_2 = con.execute(f'SELECT COUNT(*) FROM {table_name_2} ').fetchone()[0]
    count_3 = con.execute(f'SELECT COUNT(*) FROM {table_name_3} ').fetchone()[0]

    print(f"Table : {table_name_1}  nombre de lignes : {count_1}")
    print(f"Table : {table_name_2}  nombre de lignes : {count_2}")
    print(f"Table : {table_name_3}  nombre de lignes : {count_3}")
    
except AssertionError as e:
    print (f"Erreur echec du script duckdb : {e}", file=sys.stderr)
    sys.exit(1)
except Exception as e :
    print (f"Erreur echec du script duckdb: {e}", file=sys.stderr)
    sys.exit(1)
finally :
    if con is not None :
        con.close()
        #print("Close connexion insert SQL ")

print ("\n--- FIN DU PIPELINE TRAITEMENT FICHIER XLS ---")

