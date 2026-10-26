---
name: implement-slice
description: Fait implémenter le plan validé d’un ticket knitproof par un sous-agent Sonnet, un commit par étape, puis revérifie, montre le diff et ouvre la PR en brouillon après accord.
argument-hint: "[CLA-XX]"
disable-model-invocation: true
allowed-tools:
  - Bash(git branch --show-current)
---

# Implémenter le ticket $0

Branche courante : !`git branch --show-current`

Tu es la session principale. Un sous-agent Sonnet écrit le code ; tu revérifies toi-même. `<id>` est `$0` en minuscules.

## Avant de déléguer

1. `.claude/plans/<id>-plan.md` existe et Isabelle l’a validé ; sinon, arrête-toi et propose `/plan-ticket $0`.
2. La branche du frontmatter du plan existe, créée depuis `develop` à jour (`AGENTS.md`, « Branches ») ; sinon, crée-la après accord d’Isabelle.
3. `git status --short` est propre.

## Phase 5 — Implémentation

Lance l’outil Agent avec `subagent_type: general-purpose` et `model: sonnet`. Brief : la section « Brief de l’implémenteur » ci-dessous, complétée par le chemin du plan, la branche attendue et la plage d’étapes. Attends sa notification de fin.

## Phase 6 — Revérification

1. `git branch --show-current` donne la branche attendue.
2. Lance toi-même les cinq contrôles d’`AGENTS.md` (« Commandes ») ; tous verts.
3. `git log --oneline develop..` : un commit par étape, aux messages du plan, conformes aux « Conventions ».
4. `git diff develop...` : rien hors du plan ; README et `docs/` à jour selon les « Conventions ».
5. Montre à Isabelle le diff, les commits et les contrôles, et dis ce qui n’a pas été vérifié. Attends son accord.
6. Après accord : `git push -u origin <branche>` (jamais `HEAD`), puis PR en brouillon vers `develop`. Attends la CI et donne son état.

## Conditions d’arrêt

- Jamais de push ni de PR sans accord explicite d’Isabelle ; jamais de merge.
- Un contrôle rouge à la revérification : corrige avec Isabelle, dans le respect des « Règles pour tous les agents ».
- Fin : PR en brouillon et état de la CI. Isabelle merge.

## Brief de l’implémenteur

> Tu exécutes un plan validé sans le réviser. Tu ne vois pas la conversation : le plan et `AGENTS.md` font foi, en particulier « Commandes », « Règles pour tous les agents », « Branches » et « Conventions ».
>
> Pour chaque étape de la plage, dans l’ordre :
> 1. TDD quand l’étape touche du code : le test échoue d’abord, puis passe.
> 2. Applique le contenu du plan.
> 3. Mets à jour README et `docs/` dans l’étape, selon la règle de doc des « Conventions ».
> 4. Lance les cinq contrôles des « Commandes » ; tous verts.
> 5. `git branch --show-current` donne la branche attendue, juste avant le commit.
> 6. `git add <chemin>` fichier par fichier, jamais `-A`, `.` ni `-f`.
> 7. `git commit -m "<message du plan>"`, jamais `--no-verify`.
>
> Interdits : push, merge, rebase, changement de branche, écriture dans Linear.
>
> Arrête-toi et rends la main si :
> - une étape est ambiguë ou contredit `AGENTS.md` ;
> - un contrôle reste rouge après deux essais ;
> - la branche n’est pas la bonne ;
> - la plage est faite.
>
> Retour, 15 lignes au plus :
> - les commits (SHA court et message) ;
> - l’état des cinq contrôles ;
> - les écarts au plan, avec leur raison ;
> - la raison de l’arrêt.
