# Décisions d’architecture (ADR)

Une décision structurante par fichier, numérotée : `0001-titre.md`.

Seulement pour le produit et le code. Une règle de process (skills, branches, revue) vit dans le skill ou dans `AGENTS.md`, sans ADR.

Un ADR dit pourquoi on a décidé, pour ne pas refaire le débat. Il tient en 40 lignes au plus :

- **Contexte** : le problème, en quelques lignes.
- **Décision** : ce qui est décidé, par qui et quand ; au plus un tableau des valeurs retenues.
- **Alternatives écartées** : une ligne chacune, avec la raison.
- **Conséquences** : ce que la décision change, sans numéros de ligne.
- **Sources** : une ligne par source (auteur, titre, page ou URL, date de lecture).

`tests/test_adr_format.py` vérifie trois points : 40 lignes au plus, pas de section « Suites », pas de numéro de ligne ; les ADR en attente de CLA-122 y sont exemptés, et la liste ne fait que diminuer.

Pas de données brutes (mesures par taille, citations longues) : elles vont dans `src/knitproof/library/data/`, au format de son `README.md`, avec leur source, et l’ADR y renvoie. Pas de consignes d’édition de la doc : le diff les montre. Pas de tableau de suites : les liens sont dans Linear.
