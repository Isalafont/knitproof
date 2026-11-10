# ADR 0013 — Format YAML figé et poursuite sur le compte calculé

Complète l’[ADR 0003](0003-format-intermediaire-type.md) et l’[ADR 0004](0004-moteur-deterministe-sans-llm.md).

Terminologie amendée par [ADR 0014](0014-rang-plutot-que-tour-dans-les-textes.md).

## Contexte

La tranche 1 (CLA-64) livre la vérification des comptes de mailles. Elle doit charger les exemples YAML et décider quoi faire d’un compte annoncé faux : continuer sur l’annoncé ou sur le calculé.

## Décision

1. Le format YAML des patrons est figé : celui de `examples/bonnet-erreur-rang-33.yaml`, décrit à la section 9 de `architecture.md`. Un patron se charge par `yaml.safe_load` puis `Pattern.model_validate`. Une opération inconnue ou une clé en trop est rejetée par Pydantic ; la tranche 6 réutilise ce format.
2. Après un `count_mismatch`, la simulation continue sur le compte calculé, pas sur l’annoncé. Le moteur prouve, il ne croit pas l’annonce.

## Alternatives écartées

- Continuer sur le compte annoncé : pas de cascade, mais le moteur adopterait un nombre qu’il n’a pas prouvé.
- Laisser le format provisoire : les tranches suivantes (CLI, bibliothèque) s’appuieraient sur un format mouvant.

## Conséquences

- Un tour écrit pour le compte annoncé, après un `count_mismatch`, déclenche un `repeat_not_fitting` en cascade ; la simulation s’arrête alors.
- Un compte annoncé situé après l’arrêt n’est pas comparé : le rapport d’un patron cassé tôt n’affiche pas tous ses écarts.
- Toute nouvelle opération entre dans `Stitch` et dans `_op_kind` (`domain/pattern.py`), sinon elle est rejetée ; les tests de rejet le gardent.
