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
      kind: reference_measurement    # ou fiber_library, person_decision
      reference: Auteur, titre, URL
      read_on: 2026-11-09            # date de lecture, AAAA-MM-JJ
      location: tableau 2, p. 3      # facultatif
```

`knitproof.library.loader.load_library` type chaque fichier par son modèle d’entrée, déclaré dans `REGISTRY` (nom de fichier vers modèle, `library/loader.py`) : un `*.yaml` absent du registre est refusé, et une erreur nomme `fichier:id`. Un décimal s’écrit en chaîne (`"50.5"`) ou en entier nu, jamais `1e3`, `1,5` ni un flottant. La sorte `model_inference` est refusée dans les données. Une entrée `status: to_verify` donne une provenance « À VÉRIFIER » (`Provenance.to_verify`).
