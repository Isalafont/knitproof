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

`knitproof.library.loader.load_library` type chaque fichier par son modèle d’entrée, déclaré dans `REGISTRY` (nom de fichier vers modèle, `library/loader.py`) : un `*.yaml` absent du registre est refusé, et une erreur nomme `fichier:id`. Un décimal s’écrit en chaîne (`"50.5"`) ou en entier nu, jamais `1e3`, `1,5` ni un flottant. La sorte `model_inference` et la clé `extracted_by` (trace d’une lecture par un modèle) sont refusées dans les données. Une entrée `status: to_verify` donne une provenance « À VÉRIFIER » (`Provenance.to_verify`).

## Fichiers livrés

| Fichier | Modèle d’entrée | Contenu |
|---|---|---|
| `0019-calotte-du-bonnet.yaml` | `CrownRule` | les seuils de la calotte (8 diminutions par rang, dernier rang sous 24 m, montage minimal 32 m, 3 derniers rangs à chaque rang) ; `person_decision`, sans source publiée |
| `0020-hauteur-finie-et-bord-replie.yaml` | `ReferenceMeasurement` | les 12 lignes de la table Knit Picks, hauteur en pouces ; bornes d’âge (mois) pour les 4 lignes à âge chiffré seulement |
| `0021-table-de-reference-des-tailles-d-aiguilles.yaml` | `NeedleTableRow` | une ligne par taille US (22), UK (17) et JP (16) : un ou deux mm publiés, une source par système (Craft Yarn Council, Sheep and Stitch, Clover), `status: to_verify` selon l’ADR ; JP en entier À VÉRIFIER |
| `0023-longueur-des-aiguilles-circulaires-et-magic-loop.yaml` | `MagicLoopAdvice` | câble de 80 cm pour le magic loop, un conseil et non une règle, avec ses sources KnitPro et Knit Picks |
| `0024-aisance-du-bonnet.yaml` | `EaseSource` | Oslo (7 tailles : plage de tête, montage, échantillon) et Rosebud (une taille : plage de tête, tour du bord publié) ; données brutes, le % est calculé par `engine/ease.py` ; chaque `swatch` porte son point (`stitch`) ; une source peut nommer ses laines (`yarns`) et son `role` (`proposal` par défaut, ou `landmark` avec `role_reason`) |
| `0027-tour-de-tete-par-age-d-apres-les-patrons.yaml` | `ReferenceMeasurement` | plages de tour de tête par tranche d’âge (bornes en mois incluses, cm), sans valeur proposée |
| `0031-aisance-d-apres-les-patrons.yaml` | `EaseSource` | les patrons relus d’après lesquels le moteur propose l’aisance : sept patrons DROPS, Purl Soho, Barley, Simple Baby Hat, Tegan ; `role: proposal` (trois patrons DROPS en côtes 2/2) ou `landmark` avec `role_reason` ; `low == high` dans `head` note une valeur unique publiée (Barley) ; les tailles de prématurés n’y entrent pas ; montages tirés des transcriptions privées, jamais versionnées |
| `0031-aisance-de-base.yaml` | `BaseEase` | −5 % pour un bonnet ajusté à bord en côtes, échantillon en jersey ; `person_decision`, `to_verify` |
| `0030-fibres.yaml` | `Fiber` | le vocabulaire des fibres : un `id` et les noms lus sur les étiquettes des fabricants (un nom n’y figure que s’il est le terme d’étiquette d’une laine chargée, sauf `alpaca`, décision d’Isabelle) ; `person_decision` (Isabelle, 12/11/2026), sans chiffre ni avertissement ; un nom désigne une seule fibre, tous fichiers confondus |
| `0030-laines-de-reference.yaml` | `Yarn` | dix laines relues chez leur fabricant le 12/11/2026 (DROPS, Filcolana, Sandnes Garn), valeurs telles qu’écrites, adresse de la page en `reference` ; une valeur que la page ne donne pas est absente (`superwash: null`, pas de `care` pour Tynn Silk Mohair, jamais de rangs pour Sandnes Garn) ; l’échantillon des trois Sandnes Garn vient de leur fiche Ravelry lue à la main (nommée dans `location`) ; `swatches` vide ; chaque fibre d’une composition est un `id` de `0030-fibres.yaml`, sinon le chargement échoue ; les autres laines des patrons entrent au besoin, une à une |
