# ADR 0011 — Licence de l’API Ravelry

## Contexte

M2 utilise Ravelry pour pré-remplir la fiche d’un fil (CLA-54). La couche `sources` est optionnelle.

Source : la licence de l’API Ravelry v1.0 du 6 novembre 2020, lue le 25/10/2026 par Isabelle avec son compte, et résumée dans [CLA-54](https://linear.app/claude-personnal/issue/CLA-54/utiliser-lapi-ravelry-comme-source-de-fils). La licence n’a pas d’URL publique : les pages de l’API sont derrière une connexion.

## Décision

Respecter la licence. Ce sont exactement ses huit contraintes, sans ajout :

1. contacter api@ravelry.com avant toute démo publique ; le développement et les tests privés sont permis ;
2. aucun contenu d’utilisateurs : seulement les données factuelles des fils ;
3. pas de redistribution, aucune donnée Ravelry en masse dans le dépôt ;
4. effacement sur demande de Ravelry ou du propriétaire, données dérivées comprises (purge par provenance `ravelry`) ;
5. conservation limitée au strict nécessaire, et information des utilisateurs ;
6. usage commercial réservé aux applications dont le public principal est celui de Ravelry, sauf accord exprès ;
7. l’interface dit que knitproof n’est ni Ravelry ni approuvé par Ravelry ;
8. l’API est fournie sans garantie, donc l’adaptateur est optionnel.

Les identifiants restent dans `.env`.

## Alternatives écartées

- Sans Ravelry, saisie manuelle seule : plus de friction, et pas de contrôle croisé avec l’étiquette.
- Copier les données Ravelry dans la bibliothèque versionnée : contraire aux contraintes 3 et 4.

## Conséquences

- Provenance `ravelry` avec `reference` obligatoire (architecture §6).
- Effacement par source ([ADR 0008](0008-provenance-et-resolution.md)).
- knitproof fonctionne sans Ravelry.
- Une démo publique (M3) attend la réponse d’api@ravelry.com.
- La mention « ni Ravelry ni approuvé par Ravelry » est à prévoir dans l’interface ([ADR 0006](0006-portes-http-fastapi-et-react-aria.md)).
