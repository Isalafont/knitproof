# ADR 0027 — Tour de tête par âge, d’après des patrons

Amende l’[ADR 0018](0018-tour-de-tete-par-age.md) (§2, 3, 4, 5, 6 et 8).

## Contexte

L’ADR 0018 retenait les tables de l’OMS, de 0 à 60 mois. Leur licence est non commerciale et à partage identique, alors que celle du dépôt est MIT. Isabelle choisit la simplicité : des tailles que des patrons de bonnet publient, par tranche d’âge.

## Décision

Décidé par Isabelle le 09/11/2026 (CLA-67).

1. **Source (§2).** Le tour de tête par âge vient des patrons qu’Isabelle a partagés : valeurs reprises seules, avec la référence du patron. Le Craft Yarn Council ne sert qu’aux adultes, sa page ne donnant aucun âge.
2. **Grain (§8).** Une plage par tranche d’âge, bornes incluses, dans l’unité d’origine (cm). L’âge reste saisi en mois avant 2 ans, en années entières ensuite.
3. **Valeur (§3, §4).** La plage est publiée telle quelle, « À VÉRIFIER », sans valeur proposée : aucune source ne publie de milieu. La question en attente affiche la plage et demande la mesure.
4. **Adultes (§6).** Dès 15 ans, femme 53–58,5 cm et homme 56–61 cm ; sans sexe saisi, les deux plages.
5. **Sources par tranche (§5).** Chaque tranche cite le ou les patrons qui la donnent. Les tranches sont dans `src/knitproof/library/data/0027-tour-de-tete-par-age-d-apres-les-patrons.yaml`.

## Alternatives écartées

- OMS : licence non commerciale, et plage de population plus qu’une taille de bonnet.
- Milieu de la plage : une valeur que la source ne publie pas (ADR 0020, même raison).
- Catégories du Craft Yarn Council rattachées à un âge : la page n’en donne aucun, écarté par Isabelle avant 15 ans.

## Conséquences

- La grille de l’ADR 0026 repose sur l’OMS de 0 à 4 ans : CLA-118 se recadre.
- La résolution du tour de tête reste à CLA-66 ; elle ne peut proposer que la plage.
- Les en-têtes de l’ADR 0018 et l’architecture (§6, §7) disent la nouvelle source.

## Sources

- DROPS Children 37-16, 41-27, 49-25 : patrons partagés par Isabelle, valeurs reprises seules.
- Julie Taylor, *Tegan Top Knot*, tableau « Head Circumference » : patron partagé par Isabelle.
- Craft Yarn Council, « Head Circumference Chart – Yarn Standards », <https://www.craftyarncouncil.com/standards/head-circumference-chart>, lu le 09/11/2026 : la page actuelle fait foi, pas le PDF de 2015 ni l’ancienne URL `node/39`.
