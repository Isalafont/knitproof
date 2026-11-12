# ADR 0032 — Protocole d’évaluation figé

## Contexte

Le protocole d’évaluation laissait trois questions ouvertes (tolérance du montage, taille des jeux, tolérances par champ) et aucun garde-fou contre l’ajustement d’une valeur attendue après coup.

## Décision

Décisions d’Isabelle du 12/11/2026.

| Point | Valeur |
|---|---|
| Montage correct | tour fini à ±1 cm du tour visé |
| Taille des jeux | 5 cas `dev` et 15 cas `test` par évaluation |
| Lecture juste | exacte par champ, aucune tolérance |
| Données | `evals/data/<split>/`, un manifeste haché par split, vérifié par pytest |

## Alternatives écartées

- **±2 cm** : trop indulgent pour le LLM seul.
- **Égalité en mailles** : knitproof gagnerait par construction.
- **10 et 20 cas** : 90 cas à annoter, risque sur la date du 4/12.
- **±1 % sur le métrage** : une étiquette imprime des valeurs, pas des mesures.
- **Hachage des octets du YAML** : sensible à la mise en forme.

## Conséquences

- ±1 cm couvre l’arrondi au demi-rapport (côtes 2/2 à 20 m/10 cm) ; 96 m (48 cm) et 120 m (60 cm) ratent les 43,2 cm visés.
- Le champ `version` du manifeste n’est pas contrôlé, et le nom du fichier n’est pas comparé à l’`id`.
- Toute réécriture d’une valeur attendue rougit les tests.

## Sources

- `docs/evaluation.md` ; README (sortie du bonnet de 3 ans) ; décision d’Isabelle du 12/11/2026.
