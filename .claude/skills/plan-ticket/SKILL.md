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
   - un vérificateur de doc neuf (`model: sonnet`) reçoit la section « Brief du vérificateur de doc » ci-dessous, l’identifiant `$0` et le chemin du contexte.
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

Rédige `<id>-linear.md` au template de son type, aligné sur le contexte validé, et montre-le à Isabelle. Ne le publie avec l’outil Linear de la session qu’après son accord explicite.

- Templates : `${CLAUDE_SKILL_DIR}/templates/` — `us.md` (fonctionnalité), `ts.md` (technique, outillage, dette), `bug.md` (anomalie), `cadrage.md` (question à trancher, sans code). Titre au préfixe du type : `US — …`, `TS — …`, `Bug — …`, `[Cadrage] … — …`.
- Toutes les sections du template restent, une ligne sans objet porte « aucune » ou « sans objet ».
- Les critères d’acceptation reprennent ceux du contexte validé, en tableau `Étant donné | Quand | Alors`, cases d’état décochées. État producteur : coché par l’implémenteur ; état testeur : par la revérification de la session, puis par Isabelle.
- Priorité, estimation, labels et relations vont dans les champs Linear, pas dans la description.

## Conditions d’arrêt

- Aucune branche, aucun commit, aucun fichier hors de `.claude/plans/` et du scratchpad.
- Rien dans Linear sans accord explicite d’Isabelle.
- Fin : plan validé par Isabelle, ticket réaligné. L’implémentation se lance avec `/implement-slice $0`.
- Règles du projet : `AGENTS.md`, « Règles pour tous les agents » et « Conventions ».

## Brief du vérificateur de doc

> Tu vérifies les faits du contexte reçu, d’`AGENTS.md` et de la liste « à vérifier » si tu en reçois une. Un fait sur un outil (option, comportement, version) se vérifie dans sa documentation officielle, et seulement là. Un fait sur le projet se vérifie dans le ticket et dans les tickets qui lui sont directement liés, sans suivre leurs propres liens. Avant de répondre « introuvable », indiquer quelles sources ont été lues. Quand un fait est trouvé, citer sa source (URL de la doc ou identifiant du ticket). Tu lis Linear avec l’outil de la session, en lecture seule. Tu peux essayer une syntaxe sur une copie dans le scratchpad, jamais dans le dépôt.
>
> Interdits : aucune modification du dépôt, aucune écriture dans Linear.
>
> Retour, 20 lignes au plus. Pour chaque point : l’affirmation, « confirmé », « faux » ou « introuvable », la source (URL ou identifiant du ticket) et la date de lecture ; pour « introuvable », les sources lues.

## Brief de l’intégrateur

> Tu reportes dans les fichiers reçus les décisions reçues, exactement, et rien d’autre : ni ajout, ni reformulation hors de ces décisions. Une décision ambiguë, ou qui contredit un autre passage : ne tranche pas, signale-la. Remplis `revised:` avec la date et « arbitrages d’Isabelle ».
>
> Interdits : aucun fichier hors de ceux reçus, aucune branche, aucun commit, rien dans Linear.
>
> Retour, 10 lignes au plus :
> - pour chaque décision, le fichier et la section modifiés ;
> - les décisions non reportées, et pourquoi.
