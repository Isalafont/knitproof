---
name: implement-slice
description: Fait implémenter le plan validé d’un ticket knitproof par un sous-agent Sonnet, un commit par étape, puis revérifie, fait relire le diff par un agent neuf, coche les cases producteur du ticket Linear, pousse, ouvre la PR, puis coche les cases testeur et la DOD et la merge après le « ok » d’Isabelle sur le test.
argument-hint: "[CLA-XX]"
disable-model-invocation: true
allowed-tools:
  - Bash(git branch --show-current)
---

# Implémenter le ticket $0

Branche courante : !`git branch --show-current`

Tu es la session principale. Un sous-agent Sonnet écrit le code ; tu revérifies toi-même. `<id>` est `$0` en minuscules.

**En worktree** : `git rev-parse --git-dir` diffère de `git rev-parse --git-common-dir`.

## Avant de déléguer

1. `.claude/plans/<id>-plan.md` existe et Isabelle l’a validé ; sinon, arrête-toi et propose `/plan-ticket $0`.
2. La branche du frontmatter du plan existe, créée depuis `develop` à jour (`AGENTS.md`, « Branches ») ; sinon, crée-la.
3. `git status --short` est propre.

## Phase 5 — Implémentation

Lance l’outil Agent avec `subagent_type: general-purpose` et `model: sonnet`. Brief : la section « Brief de l’implémenteur » ci-dessous, complétée par le chemin du plan, la branche attendue et la plage d’étapes. Attends sa notification de fin.

## Phase 6 — Revérification

1. `git branch --show-current` donne la branche attendue.
2. Lance toi-même les cinq contrôles d’`AGENTS.md` (« Commandes ») ; tous verts.
3. D’abord `git fetch origin develop`, puis `git log --oneline origin/develop..` : un commit par étape, aux messages du plan, conformes aux « Conventions ».
4. `git diff origin/develop...` : rien hors du plan ; README et `docs/` à jour selon les « Conventions ».
5. Relecture du diff par un agent neuf (`model: opus`), en arrière-plan : brief `${CLAUDE_SKILL_DIR}/reviewer.md`. Il reçoit seulement l’identifiant, les chemins du plan validé et du contexte, et la plage `origin/develop..<branche>` (base = `git merge-base origin/develop <branche>`, en SHA, et tête). Pas de seconde relecture après un rebase. Jamais les tableaux d’arbitrage de la planification, ni ton avis. Quand il revient, dresse le tableau d’arbitrage : constat, « vérifié par », ta recommandation. Un constat sans preuve ne va pas plus loin. Isabelle tranche chaque ligne ; l’implémenteur fait les corrections retenues (fixup sur le commit de l’étape concernée), puis reprends aux étapes 1 à 4. Une seule relecture par ticket : la relancer est une décision d’Isabelle.
6. Cases producteur : pour chaque CA, et chaque RG s’il y en a, lance la commande ou le test qui la prouve ; coche OK en état producteur seulement s’il passe, sinon KO et arrête-toi. Corrige les mentions devenues fausses (par exemple « ADR à créer »). Montre à Isabelle chaque case avec sa preuve et la description modifiée ; publie-la avec l’outil Linear de la session seulement après son accord.
7. `git push -u origin <branche>` (jamais `HEAD`), puis PR prête (pas de brouillon) vers `develop`, avec une section « Tester ». Attends la CI ; verte, passe le ticket en « In Review » avec l’outil Linear de la session.
8. En worktree, juste avant de donner le test, rebase si `develop` a avancé. Donne à Isabelle le lien de la PR, l’état de la CI, les commits, les contrôles, les cases producteur et ce qui n’a pas été vérifié. Attends son « ok » sur le test.
9. Après son « ok » et ses contrôles, au plus tard au merge : coche les cases testeur des CA et des RG, puis la DOD, chaque case après sa preuve (DOD : les cinq contrôles, README et `docs/` à jour, ADR créée si une décision structurante est prise). Même accord avant de publier.
10. Juste avant le merge, en worktree, rebase si `develop` a avancé. CI verte et cases publiées : `gh pr merge <numéro> --merge`. Après le merge : en worktree, aucun geste git (la branche reste ouverte ici, le nettoyage ne se fait pas depuis ce dossier) ; sinon, `git switch develop`, `git pull --ff-only origin develop` et `git branch -d <branche>`.

## Rebase en worktree

1. `git fetch origin develop`, jamais `git fetch origin` : déplacer `origin/<branche>` annulerait la protection du lease. `git merge-base --is-ancestor origin/develop HEAD` réussit : rien à faire.
2. Sinon, `git rebase origin/develop`. Résous toi-même un conflit sur `docs/plan.md` ; tout autre conflit s’arbitre avec Isabelle. Relance les cinq contrôles.
3. Branche déjà poussée : `git push --force-with-lease origin <branche>`, jamais `--force` ni `-f`, puis attends la CI. Une commande à la fois : pas de `git rebase … && git push …`, qui demande une autorisation par sous-commande. Un rejet du lease veut dire qu’un autre a poussé : arrête-toi et montre-le à Isabelle.
4. Après son « ok » : rebase sans conflit et CI reverte, le « ok » tient ; conflit résolu, redemande son « ok » avant le merge. À l’étape 10, signale-lui que ce nouveau « ok » est demandé alors que les cases testeur sont déjà publiées à l’étape 9.

## Conditions d’arrêt

- Jamais de merge sans le « ok » d’Isabelle sur le test, ni avec une CI rouge ; jamais de merge vers `main`.
- Un contrôle rouge à la revérification : corrige avec Isabelle, dans le respect des « Règles pour tous les agents ».
- Jamais de case cochée sans la commande ou le test qui la prouve ; jamais d’écriture dans Linear sans l’accord d’Isabelle, sauf le passage en « In Review » de l’étape 7.
- Si le test d’Isabelle demande des corrections, le lui signaler : elle décide du statut du ticket, sans retour automatique en « In Progress ».
- La DOR n’est pas cochée ici : `/plan-ticket` la coche à la publication du ticket réaligné.
- Fin : PR mergée dans `develop` ; branche locale supprimée, sauf en worktree où l’orchestrateur s’en charge.

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
