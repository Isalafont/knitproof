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

## Fichiers livrés

| Fichier | Modèle d’entrée | Contenu |
|---|---|---|
| `0020-hauteur-finie-et-bord-replie.yaml` | `ReferenceMeasurement` | les 12 lignes de la table Knit Picks, hauteur en pouces ; bornes d’âge (mois) pour les 4 lignes à âge chiffré seulement |
| `0021-table-de-reference-des-tailles-d-aiguilles.yaml` | `NeedleTableRow` | une ligne par taille US (22), UK (17) et JP (16) : un ou deux mm publiés, une source par système (Craft Yarn Council, Sheep and Stitch, Clover), `status: to_verify` selon l’ADR ; JP en entier À VÉRIFIER |
| `0024-aisance-du-bonnet.yaml` | `EaseSource` | Oslo (7 tailles : plage de tête, montage, échantillon) et Rosebud (une taille : plage de tête, tour du bord publié) ; données brutes, le % est calculé par `engine/ease.py` |
| `0027-tour-de-tete-par-age-d-apres-les-patrons.yaml` | `ReferenceMeasurement` | plages de tour de tête par tranche d’âge (bornes en mois incluses, cm), sans valeur proposée |
