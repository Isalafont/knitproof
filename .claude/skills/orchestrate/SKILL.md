---
name: orchestrate
description: Lance les tickets knitproof démarrables en parallèle, chacun dans son worktree et sa pane herdr, sans changer les validations d’Isabelle.
argument-hint: "[--max N]"
disable-model-invocation: true
allowed-tools:
  - Bash(git branch --show-current)
  - Bash(printenv HERDR_ENV)
  - Bash(true)
---

# Orchestrer les tickets

Arguments : $ARGUMENTS. Limite : `--max N`, 3 par défaut, sans plafond fixe.

Branche courante : !`git branch --show-current`
`HERDR_ENV` : !`printenv HERDR_ENV || true`

Tu es la session principale, dans le checkout principal. Tu ne planifies ni n’implémentes. `<id>` est l’identifiant en minuscules.

## Au démarrage

Arrête-toi en disant pourquoi si l’un de ces points échoue :
1. `HERDR_ENV` vaut `1`. Le succès d’une commande herdr ne le prouve pas.
2. La branche courante est `develop` et `git status --short` est propre.
3. Le statut « Attente Isabelle » existe (outil Linear de la session, équipe « Claude personnal »).

## Sélection

1. `git pull --ff-only origin develop`, toujours avec ces arguments : un `git fetch origin` ou un `git pull` sans argument déplacerait les références des autres worktrees et annulerait leur lease.
2. Lis les tickets du projet knitproof, du cycle en cours, au statut Todo, triés par priorité ; « No priority » (valeur 0 dans Linear) passe après les autres. Écarte ceux qui ont déjà un fichier `.claude/plans/<id>-orchestration.md`.
3. Pour chacun, lis ses bloqueurs et le statut de chacun. Un seul bloqueur non terminé l’écarte : nomme-le.
4. Une place est prise par chaque `.claude/plans/*-orchestration.md` sans ligne `nettoye:` ni `abandon:`.
5. Propose à Isabelle les tickets retenus dans la limite, ceux en attente de place et ceux écartés avec leur bloqueur. Au-delà de 3 tickets sur du code (titre sans le préfixe `[Cadrage]`), avertis sans refuser. Tant que les plans ne prouvent pas des fichiers différents, recommande 2 ou 3. Rien ne part sans sa validation.

## Lancement, ticket par ticket

Variables : `R`, racine du checkout principal ; `W`, `<dossier parent de R>/knitproof-<id>` ; `B`, branche du ticket Linear.

1. Numéro d’ADR : le plus grand entre `git ls-tree --name-only origin/develop docs/adr/` et les lignes `adr:` de `.claude/plans/*-orchestration.md`, plus un, sur quatre chiffres.
2. `git worktree add --no-track -b B W origin/develop`, ou `git worktree add W B` si `B` existe déjà. Un refus (branche extraite ailleurs) se montre à Isabelle.
3. Écris `.claude/plans/<id>-orchestration.md` : `adr:`, `worktree:`, `branche:`.
4. `ln -s R/.claude/plans W/.claude/plans`.
5. `herdr pane layout --current`, puis `herdr pane split --current --direction <right ou down> --cwd W --no-focus`, sens choisi pour éviter des panes trop étroites. Lis l’ID dans `.result.pane.pane_id`. Ajoute `pane:` au fichier d’orchestration.
6. `herdr agent start <id> --kind claude --pane <pane> -- --add-dir R/.claude/plans`. Si le retour est `agent_not_ready`, montre l’écran à Isabelle.
7. `herdr agent prompt <id> "/plan-ticket CLA-XX orchestre <adr>" --wait --until working --timeout 30000`, puis `herdr agent read <id>` : si le skill n’a pas démarré, donne à Isabelle la commande à saisir dans la pane.

## Suivi

Attends avec l’outil Monitor, sur une boucle qui affiche une ligne quand un fichier d’orchestration gagne `plan_valide:` ou `merge:`. Si la boucle ne convient pas, Isabelle te dit « suite » et tu relis ces fichiers. Isabelle répond dans chaque pane. Tu ne réponds jamais à sa place : pas de `herdr agent send-keys`.

- `plan_valide:` : si le fichier n’a pas de ligne `implementation:`, ajoute `implementation: AAAA-MM-JJ`, puis `herdr agent prompt <id> "/implement-slice CLA-XX orchestre" --wait --until working --timeout 30000`, puis `herdr agent read <id>`. Si le retour est `agent_blocked`, attends. Si le skill ne démarre pas, donne à Isabelle la commande à saisir dans la pane.
- `merge:` : nettoie, puis reprends à « Sélection » pour la place libérée, avec la validation d’Isabelle.

## Nettoyage

Dans cet ordre, depuis le checkout principal :
1. `gh pr view <branche> --json mergedAt` donne une date ; sinon, arrête-toi.
2. `herdr pane close <pane>`.
3. `git worktree remove W`, jamais `--force` : un refus se montre à Isabelle.
4. `git pull --ff-only origin develop`, `git branch -d B`.
5. Ajoute `nettoye: AAAA-MM-JJ` au fichier d’orchestration, conservé pour ne pas réutiliser son numéro d’ADR.
6. Quand plus aucun worktree n’est ouvert, `git fetch -p origin` retire les références périmées.

## Abandon

Sur demande d’Isabelle, pour un ticket abandonné : nettoyage sans contrôle de merge, soit les étapes 2 à 4 de « Nettoyage », puis ajoute `abandon: AAAA-MM-JJ` au fichier d’orchestration, ce qui libère sa place. Un `git branch -d` qui refuse se montre à Isabelle ; jamais `-D`.

## Conditions d’arrêt

- Aucun merge ici : `/implement-slice` merge, après le « ok » d’Isabelle et une CI verte.
- Aucune écriture Linear ici.
- `--force`, `-f`, `git branch -D`, `git worktree remove --force` : jamais.
- Une session relancée reprend depuis les fichiers d’orchestration.
- Fin : plus de ticket retenu ni de place occupée, ou arrêt demandé par Isabelle.
