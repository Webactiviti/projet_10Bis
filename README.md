Mettez en place un pipiline d'orchestration des flux

## contenu du repository

* Mise en service sur une base  Docker avec installation de Kestra

* scripts python de nettoyage et l'exploration des données et enregistrement des données dans duckdb

* flow code pour Kestra avec cron pour le 15 du mois à 9h


* test en local des scripts

uv run python ./scripts/insert_xls.py 
uv run python ./scripts/resultat_req.py


* création du docker

sudo docker compose up -d


* built
 
sudo docker build -t dock_prj10_bis .

ou

sudo docker build --no-cache -t dock_prj10_bis .



* URL accès Kestra ( port définie dans le docker-compose.yml)

http://localhost:8080


* autres commandes docker

sudo docker images    //  affiche les docker présent


sudo docker rmi -f $(docker images "name_project" )   // supprime le docker name_project

* DashBoard Kestra



## 📂 Structure du Répertoire

```text
projet_10/

├── docker-compose.yml                              # Orchestration des conteneurs 
├── Dockerfile                                      # Configuration du conteneur 
├──                                 # flow code pour Kestra 
├── pyproject.toml                                  # Gestion des dépendances Python (uv)
├── doc                                             # répertoire  de document 
|    └── dico_data.xlsx                             # dictionnaire des fichiers de données
├── data                                            # répertoire des données 
|    └── exports                                    # répertoire des fichiers générés
|    └── processed                                  # répertoire  fichier duckdb
├── scripts                                         # répertoire des scripts python 
|    └── insert_xls.py                              # fichier python insertion des données
|    └── resultat_req.py                            # fichier python génération des rapport csv et xlsx
├── img                                             # répertoire  images 
└── README.md                                       # Documentation du projet
```
