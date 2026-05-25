# Métro Paris

Projet Streamlit pour explorer un réseau GTFS et calculer des itinéraires.

## Prerequis

- Python 3.10 ou plus récent
- Les dépendances installées avec `pip install -r requirements.txt`
- Le jeu de données GTFS d'Ile-de-France Mobilites : https://data.iledefrance-mobilites.fr/explore/dataset/offre-horaires-tc-gtfs-idfm/information/

## Installation

```bash
pip install -r requirements.txt
```

## Pretraitement des donnees

Téléchargez le GTFS puis placez le dossier à la racine du projet, par exemple `GTFS/`.

Ensuite, genere le fichier pretraité utilisé par l'application :

```bash
python preprocess.py GTFS GTFS_preprocessed.json.gz --route-types 1 2
```

Vous pouvez aussi générer une version non compressée en utilisant `GTFS_preprocessed.json`.

## Lancer l'application

Une fois le prétraitement terminé, démarrez l'interface Streamlit :

```bash
streamlit run app.py
```

L'application charge automatiquement `GTFS_preprocessed.json.gz` s'il existe, sinon `GTFS_preprocessed.json`.
