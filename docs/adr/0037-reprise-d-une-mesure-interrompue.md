# ADR 0037 — Reprise d’une mesure interrompue

Précise l’[ADR 0036](0036-reessai-sur-erreur-passagere.md) (« Épuisement ») et complète l’[ADR 0035](0035-ligne-de-base-llm-seul.md).

## Contexte

Une erreur du fournisseur arrêtait `eval` sans rien garder : les réponses déjà payées étaient perdues. La mesure `test` coûte cinq modèles à 45 passages, et un quota épuisé l’arrêtera volontairement.

## Décision

Décision d’Isabelle du 18/11/2026.

- **Journal** : `<horodatage>-<split>.partial.jsonl` dans le dossier des résultats, en JSON Lines. Une ligne d’en-tête (split, prompt, passages, hachages des cas, entrées résolues), puis une ligne par passage, vidée sur disque avant l’appel suivant. Il naît au premier passage : un arrêt au premier appel ne laisse aucun fichier.
- **Reprise** : `--resume <journal>`. Seuls les passages absents appellent un modèle ; un passage refusé est une réponse, jamais rappelé. Tout arrêt est repris, 400 et 401 compris.
- **Contrôles** : un en-tête qui diffère par le prompt, les passages, le split, les cas ou les entrées refuse la reprise, en nommant le champ, avant tout appel.
- **Une seule mesure** : `measured_on` et le nom du YAML sont ceux du premier lancement ; chaque passage garde son `at`. Une mesure reprise vaut pour la publication `test`.
- **Fin** : le YAML daté, au format inchangé, s’écrit puis le journal est supprimé. Le YAML daté existant est refusé avant tout appel.
- **Ligne finale** : coupée ou illisible, elle est ignorée et retirée ; une autre ligne illisible refuse la reprise.

## Alternatives écartées

- **YAML multi-documents** : ligne tronquée ambiguë.
- **Reprise implicite du dernier journal** : une surprise de plus ; le chemin se donne.
- **Journal né avant le premier appel** : change les tests « dossier vide » sans rien garder de plus.

## Conséquences

- La règle « aucun résultat partiel » de l’ADR 0036 vaut pour le YAML : le journal est un acquis, jamais un résultat.
- `fsync` protège d’un arrêt du processus, pas d’une coupure de courant : le passage perdu est rappelé une fois.
- Le rejeu en CI reste à faire.

## Sources

- Essais du 18/11/2026 : `model_dump_json` et `model_validate_json` relisent un `Decimal` et un `datetime` égaux, sur les résultats `2026-11-17T1528-dev.yaml` et `2026-11-17T1443-dev.yaml`.
