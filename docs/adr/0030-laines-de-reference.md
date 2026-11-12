# ADR 0030 — Vocabulaire des fibres et laines de référence

Remplace en partie l’[ADR 0010](0010-melanges-de-fibres.md) ; nuance l’[ADR 0011](0011-licence-api-ravelry.md).

## Contexte

La fibre ne suffit pas à dire comment un fil se comporte : la part de chaque fibre compte, et aucune source chiffrée n’existe par fibre.

## Décision

Décision d’Isabelle du 12/11/2026.

1. **La fibre est un vocabulaire** (`Fiber` : `id`, noms), sans chiffre ni avertissement. Isabelle décide quels noms désignent une même fibre ; les noms viennent des étiquettes.
2. **Une laine est un produit** (`Yarn`) : composition en pourcentages, superwash, étiquette du fabricant (`YarnLabel`), échantillons.
3. **Le comportement vient d’un échantillon de la laine**, tricoté avant et après blocage, daté, avec aiguilles et point ; la liste est vide sans échantillon. Trois échantillons distincts, chacun avec ses aiguilles : celui du fabricant, celui de la personne avant blocage, celui de la personne après blocage.
4. **Ordre des sources d’une laine** : l’étiquette, la page du fabricant, la fiche publique Ravelry lue à la main par Isabelle, une laine à la fois. Laine arrêtée : le site du fabricant s’il la garde, sinon Ravelry ; `reference` cite alors l’adresse de la fiche et `read_on` la date de lecture.
5. **Données** : `0030-fibres.yaml` (`person_decision`) et `0030-laines-de-reference.yaml` (`reference_measurement`). Une composition qui cite une fibre hors vocabulaire fait échouer le chargement.

## Alternatives écartées

- Des profils de fibres chiffrés : aucune source.
- Une moyenne pondérée des profils (ADR 0010) : plus de profils à pondérer.
- Une copie en masse ou automatique des données Ravelry (ADR 0011) : une fiche relue à la main, laine par laine, n’en est pas une ; Isabelle, titulaire du compte, l’admet.

## Conséquences

- `FiberProfile` devient `Fiber` ; la phrase de l’[ADR 0024](0024-aisance-du-bonnet.md) « la fibre ne porte que des avertissements sourcés » est remplacée.
- Ajouter une laine ou une fibre ajoute une entrée YAML, sans changer le code.

## Sources

- Décision d’Isabelle, 12/11/2026 ; pages des fabricants citées dans le YAML.
