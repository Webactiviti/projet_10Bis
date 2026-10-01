Mettez en place un pipiline d'orchestration des flux

## contenu du repository

* Mise en service sur une base  Docker avec installation de Kestra

* scripts python et requête sql sur la base duckdb

* flow code pour Kestra avec cron pour le 15 du mois à 9h


* built
 
sudo docker build -t dock_prj10_bis .

ou

sudo docker build --no-cache -t dock_prj10_bis .

* création du docker

sudo docker compose up -d


* URL accès Kestra ( port définie dans le docker-compose.yml)

http://localhost:8080


* URL accès MailPit ( port définie dans le docker-compose.yml)

http://localhost:8025


* autres commandes docker

sudo docker images    //  affiche les docker présent


sudo docker rmi -f $(docker images "name_project" )   // supprime le docker name_project



## 📂 Structure du Répertoire

```text
projet_10/

├── docker-compose.yml                              # Orchestration des conteneurs 
├── Dockerfile                                      # Configuration du conteneur 
├── read_zip_V4.yaml                                # flow code pour Kestra 
├── clear_log.yaml                                  # flow code pour Kestra effacement des logs pour debug
├── pyproject.toml                                  # Gestion des dépendances Python (uv)
├── doc                                             # répertoire  de document 
|    └── dico_data.xlsx                             # dictionnaire des fichiers de données
├── data                                            # répertoire des données 
|    └── exports                                    # répertoire des fichiers générés csv et xlsx
├── scripts                                         # répertoire des scripts python 
|    └── insert_xls.py                              # fichier python insertion des données
|    └── resultat_req.py                            # fichier python génération des rapport csv et xlsx
└── README.md                                       # Documentation du projet
```
