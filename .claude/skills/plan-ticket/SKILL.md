---
name: plan-ticket
description: Prépare le contexte et le plan d’un ticket knitproof (questions une par une, plan vérifié, deux relectures, arbitrage, ticket réaligné), sans écrire de code.
argument-hint: "[CLA-XX]"
disable-model-invocation: true
allowed-tools:
  - Bash(git branch --show-current)
---

# Planifier le ticket $0

Branche courante : !`git branch --show-current`

Tu es la session principale : tu orchestres, tu poses les questions à Isabelle, tu arbitres avec elle. Tu n’écris ni le plan ni le code.

Dans les noms de fichiers, `<id>` est `$0` en minuscules (`CLA-58` donne `cla-58`). Fichiers produits, hors git : `.claude/plans/<id>-context.md`, `.claude/plans/<id>-plan.md`, `.claude/plans/<id>-linear.md`.

Chaque sous-agent : outil Agent, `subagent_type: general-purpose`, avec le `model` indiqué à sa phase. Opus pour le rédacteur et les relecteurs, Sonnet pour le vérificateur de doc et l’intégrateur. Les briefs en fichier passent par leur chemin complet `${CLAUDE_SKILL_DIR}/…`. Attends la notification de fin d’un sous-agent avant d’utiliser son résultat ; ne résume jamais un résultat qui n’est pas revenu.

## Phase 1 — Questions (rédacteur)

1. Lance le rédacteur (`model: opus`) : brief `${CLAUDE_SKILL_DIR}/writer.md`, phase « questions », identifiant `$0`.
2. Pose ses questions à Isabelle **une par une**, en attendant chaque réponse.

## Phase 2 — Contexte, puis plan (même rédacteur)

1. Reprends le **même** rédacteur avec SendMessage (outil différé : charge-le par ToolSearch) et donne-lui les réponses : il rédige `<id>-context.md`.
2. Repli si SendMessage est indisponible : un rédacteur neuf reçoit le résumé du ticket, les questions, les réponses et les chemins des fichiers déjà écrits.
3. Montre le contexte à Isabelle. Rien ne continue sans sa validation explicite.
4. Phase « plan », dans un même message :
   - le même rédacteur, ou un neuf avec le même repli, rédige `<id>-plan.md` et marque « à vérifier » chaque version, option ou syntaxe d’outil qu’il affirme ;
   - un vérificateur de doc neuf (`model: sonnet`) reçoit la section « Brief du vérificateur de doc » ci-dessous et le chemin du contexte.
5. Quand les deux sont revenus, transmets au rédacteur les constats du vérificateur, URL comprises. Si des marques « à vérifier » restent sans constat, relance d’abord le vérificateur sur cette liste. Le rédacteur finalise alors le plan sans refaire ces vérifications.

## Phase 3 — Deux relectures en parallèle (deux agents neufs)

1. Dans un même message, lance en arrière-plan :
   - `${CLAUDE_SKILL_DIR}/reviewers/technical.md` : justesse technique ;
   - `${CLAUDE_SKILL_DIR}/reviewers/fidelity.md` : fidélité et simplicité.
2. Ne leur donne que l’identifiant et les chemins, ni ton avis ni celui de l’autre.
3. Quand les deux sont revenus, dresse le tableau d’arbitrage : correction, relecteur, ta recommandation. Isabelle tranche chaque ligne.
4. Un intégrateur neuf (`model: sonnet`) reporte les décisions. Il reçoit la section « Brief de l’intégrateur » ci-dessous, la liste exacte des décisions d’Isabelle et les chemins du plan, du contexte et de `<id>-linear.md` s’il existe déjà.
5. Le plan n’est validé que sur accord explicite d’Isabelle.

## Phase 4 — Ticket réaligné (session)

Rédige `<id>-linear.md` au canevas ci-dessous, aligné sur le contexte validé, et montre-le à Isabelle. Ne le publie avec l’outil Linear de la session qu’après son accord explicite.

```
Titre: …

## Constat
Le problème, factuel, sans solution.

## Objectif
La valeur visée.

## Proposition technique
Approche et fichiers clés, en bref.

## Critères d’acceptation
1. Étant donné …, quand …, alors …
n. Contrôles verts, doc à jour.

## Hors périmètre
- … → ticket

---

Priorité: … · Estimate: … pts · Labels: … · Lié à: … · Références: …
```

## Conditions d’arrêt

- Aucune branche, aucun commit, aucun fichier hors de `.claude/plans/` et du scratchpad.
- Rien dans Linear sans accord explicite d’Isabelle.
- Fin : plan validé par Isabelle, ticket réaligné. L’implémentation se lance avec `/implement-slice $0`.
- Règles du projet : `AGENTS.md`, « Règles pour tous les agents » et « Conventions ».

## Brief du vérificateur de doc

> Tu vérifies dans la doc officielle, et seulement là, les versions, options et syntaxes des outils nommés par le contexte reçu, par `AGENTS.md` et par la liste « à vérifier » si tu en reçois une. Tu peux essayer une syntaxe sur une copie dans le scratchpad, jamais dans le dépôt.
>
> Interdits : aucune modification du dépôt, rien dans Linear.
>
> Retour, 20 lignes au plus. Pour chaque point : l’affirmation, « confirmé », « faux » ou « introuvable », l’URL et la date de lecture.

## Brief de l’intégrateur

> Tu reportes dans les fichiers reçus les décisions reçues, exactement, et rien d’autre : ni ajout, ni reformulation hors de ces décisions. Une décision ambiguë, ou qui contredit un autre passage : ne tranche pas, signale-la. Remplis `revised:` avec la date et « arbitrages d’Isabelle ».
>
> Interdits : aucun fichier hors de ceux reçus, aucune branche, aucun commit, rien dans Linear.
>
> Retour, 10 lignes au plus :
> - pour chaque décision, le fichier et la section modifiés ;
> - les décisions non reportées, et pourquoi.
