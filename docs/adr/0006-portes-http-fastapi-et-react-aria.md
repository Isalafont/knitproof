# ADR 0006 — Portes HTTP : FastAPI, React et React Aria Components

## Contexte

- M3 demande une API JSON et une interface accessible (RGAA 4.1 AA, audit publié, axe-core en CI).
- Les deux sont des portes vers `app` (architecture §5).
- Le projet doit aussi être défendable en entretien.

## Décision

- API JSON en FastAPI : Pydantic intégré, si bien que les schémas de `domain` servent à la validation, à la documentation OpenAPI et JSON Schema, et aux sorties des modèles (journal de cadrage ; [doc](https://fastapi.tiangolo.com/features/)).
- Interface en React et React Aria Components : composants accessibles, sans style imposé, conformes aux ARIA Authoring Practices ([doc](https://react-aria.adobe.com/)). Paquet `react-aria-components`, sous licence Apache-2.0, maintenu par Adobe ([licence](https://github.com/adobe/react-spectrum/blob/main/LICENSE)).
- Organisation en atomic design (atoms, molecules, organisms), comme les ViewComponents de DataPass.
- Outillage front : [Vite](https://vite.dev/), [Vitest](https://vitest.dev/) et [Playwright](https://playwright.dev/), sans version figée ici.

## Alternatives écartées

- HTMX et Jinja : une seule application et pas de build JS, mais une démo moins valorisante sur un CV (source : ticket CLA-51).
- React et shadcn/ui (Radix) : très demandé et rapide à habiller, mais moins rigoureux en accessibilité (source : ticket CLA-51).
- DSFR ou react-dsfr : sous licence Etalab 2.0, mais d’usage réservé à l’État. Il est obligatoire pour les sites de l’État depuis le 7 juillet 2023 et interdit aux autres acteurs, publics ou privés ([périmètre d’application](https://www.systeme-de-design.gouv.fr/version-courante/fr/premiers-pas/perimetre-d-application)). Isabelle confirme le 26/10/2026 que le DSFR est réservé aux sites de l’État (la page officielle répond 403 à la lecture automatique).

## Conséquences

- Une deuxième application à maintenir, front et API.
- Le build est servi par FastAPI, à confirmer avec l’hébergeur (CLA-59) ([doc](https://fastapi.tiangolo.com/tutorial/static-files/)).
- `web` et `api` restent sans logique métier (contrats import-linter).
