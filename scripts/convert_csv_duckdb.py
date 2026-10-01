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

# Récupération du nom des fichiers
if len(sys.argv) < 4:
    print("Erreur : arguments insuffisants (3 fichiers CSV requis).")
    sys.exit(1)

# Récupération du nom du fichier
file_name1 = sys.argv[1]
file_name2 = sys.argv[2]
file_name3 = sys.argv[3]




print("--- DEBUT DU PIPELINE CSV TO DUCKDB ---\n")


db_path_duckdb ="fichiersql.duckdb"


print(f"Fichiers présents : {os.listdir('.')}")


# ---------------------------------
# Lecture des fichiers CSV
# ---------------------------------

try:
    file_path = Path(file_name1).resolve()
    df_csv1 = pd.read_csv(file_path)
    print(f"Succès ! {len(df_csv1)} lignes chargées pour {file_name1}.")

except Exception as e:
    print(f"Erreur critique lors de la lecture : {e}")
    sys.exit(1)

try:
    file_path = Path(file_name2).resolve()
    df_csv2 = pd.read_csv(file_path)
    print(f"Succès ! {len(df_csv2)} lignes chargées pour {file_name2}.")

except Exception as e:
    print(f"Erreur critique lors de la lecture : {e}")
    sys.exit(1)

try:
    file_path = Path(file_name3).resolve()
    df_csv3 = pd.read_csv(file_path)
    print(f"Succès ! {len(df_csv3)} lignes chargées pour {file_name3}.")

except Exception as e:
    print(f"Erreur critique lors de la lecture : {e}")
    sys.exit(1)


# -----------------------------------------------
# insertion dans la base duckDB des fichiers CSV
# -----------------------------------------------

con = None
try: 
    con = duckdb.connect(db_path_duckdb)
    # Enregistrement des DataFrames dans DuckDB
    nom_table1 = Path(file_name1).stem
    con.register('csv1_temp', df_csv1)
    con.execute (f"CREATE or REPLACE TABLE {nom_table1} as select * from csv1_temp" )
    
    nom_table2 = Path(file_name2).stem
    con.register('csv2_temp', df_csv2)
    con.execute (f"CREATE or REPLACE TABLE {nom_table2} as select * from csv2_temp" )
    
    nom_table3 = Path(file_name3).stem
    con.register('csv3_temp', df_csv3)
    con.execute (f"CREATE or REPLACE TABLE {nom_table3} as select * from csv3_temp " )

    con.execute ("CHECKPOINT")
    #print ("\nInsertion des fichiers terminé")
    
    
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

'''
# Vérification si les tables ont été bien créées et ont le bon nom
con =None
try:
    con = duckdb.connect(db_path_duckdb)

    query_ca = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'main';
    """
    df_table= con.execute(query_ca).df()
    print("Liste des tables duckdb :")
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

print("\n--- FIN DU PIPELINE CSV TO DUCKDB ---")
