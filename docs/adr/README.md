# Décisions d’architecture (ADR)

Une décision structurante par fichier, numérotée : `0001-titre.md`.

Un ADR dit pourquoi on a décidé, pour ne pas refaire le débat. Il tient en 40 lignes au plus :

- **Contexte** : le problème, en quelques lignes.
- **Décision** : ce qui est décidé, par qui et quand ; au plus un tableau des valeurs retenues.
- **Alternatives écartées** : une ligne chacune, avec la raison.
- **Conséquences** : ce que la décision change, sans numéros de ligne.
- **Sources** : une ligne par source (auteur, titre, page ou URL, date de lecture).

Pas de données brutes (mesures par taille, citations longues) : elles vont dans la bibliothèque YAML, avec leur source. Pas de consignes d’édition de la doc : le diff les montre. Pas de tableau de suites : les liens sont dans Linear.
