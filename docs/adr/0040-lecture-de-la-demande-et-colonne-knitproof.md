# ADR 0040 — Lecture de la demande et colonne « knitproof »

Complète l’[ADR 0035](0035-ligne-de-base-llm-seul.md) (forme du cas et verdict) et suit les ADR 0036 à 0038 (réessai, reprise, quota).

## Contexte

La ligne de base « LLM seul » est mesurée ; la colonne « knitproof » (le modèle lit, le moteur calcule) ne l’est pas, et sans elle la thèse n’a pas de chiffre. Décisions d’Isabelle du 23/11/2026 : attendu de lecture par cas, un seul ticket.

## Décision

- **Type de lecture** : `BeanieReading` (`app`), interne, tous champs facultatifs, tel que le texte le dit : tour de tête, écart ou tour fini visé, jauges par état de blocage, étiquette, aiguilles en mm, bord nommé, méthode. `calc` et `BeanieRequest` ne changent pas.
- **Conversion par le code** : `reading_inputs` (pure, `Decimal` exact) rend les entrées du moteur : tour visé, jauge, `StitchMultiple`. Elle rend `ReadingIncomplete` (valeur retournée, pas exception) quand tête, bord, ou écart et tour fini (un seul des deux) manquent ou ne se convertissent pas : le passage s’abstient.
- **Verdict** : le moteur calcule le montage depuis la lecture, jugé par `score` de la ligne de base (±1 cm, ADR 0032). Sans jauge lue, le moteur pose `gauge_missing` : abstention. Lire « à plat » est faux.
- **Provenance** : `ReadingRecord` porte la lecture et une `Provenance` `model_inference` avec `extracted_by`, `to_verify` vrai ; par lecture, pas par champ.
- **Attendu de lecture** : `EvalCase.expected_reading`, requis, ce que le texte dit et seulement cela, brouillon de l’agent signé par Isabelle ; la lecture juste se compte champ par champ, sans tolérance, les champs inventés à part (`score_reading`).
- **Deux appels par passage** : « LLM seul » puis lecture, mêmes entrées, 3 passages, un YAML ; le passage s’écrit au journal entier, et si le second appel échoue le premier est refait à la reprise.
- **Aiguilles** : lues en mm seulement ; une taille US obligerait le modèle à convertir, et les 21 `input` ne donnent que des mm.

## Alternatives écartées

- **`BeanieRequest` assoupli** : change `calc` et fait calculer l’aisance au modèle.
- **`model_inference` dans `Origin`** : un fichier de `calc` pourrait s’en réclamer sans `extracted_by`.
- **Deux mesures séparées** : le comparatif « même modèle, même entrée » ne tiendrait plus par construction.

## Conséquences

- Les 21 cas sont re-hachés ; les anciens YAML de résultats restent lisibles (champs « knitproof » facultatifs).
- Le prompt `request-reading-v1` se met au point sur `dev` seulement, puis se fige.
