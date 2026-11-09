# Données de la bibliothèque

Un fichier YAML par décision, nommé comme son ADR (`0024-aisance-du-bonnet.yaml`) ; ce nom est une convention que le test ne contrôle pas. `tests/test_library_data.py` refuse tout `*.yaml` à la racine de `data/` dont le contenu est hors format.

```yaml
schema_version: 1
decided_in: docs/adr/0024-aisance-du-bonnet.md
entries:
  - id: oslo-ajuste-jersey-3-ans    # unique dans le fichier
    head_cm: "50.5"                  # décimal en chaîne, jamais de flottant nu ; entier nu admis
    status: to_verify                # facultatif, seule valeur admise
    source:
      kind: reference_measurement    # ou fiber_library
      reference: Auteur, titre, URL
      read_on: 2026-11-09            # date de lecture, AAAA-MM-JJ
      location: tableau 2, p. 3      # facultatif
```

Les champs métier de chaque entrée sont libres ici : CLA-67 les type au chargement. Une entrée `status: to_verify` peut être livrée ; CLA-67 en fera une hypothèse « À VÉRIFIER ».
