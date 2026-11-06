---
name: plan-ticket
description: Prépare le contexte et le plan d’un ticket knitproof (questions métier seules posées, plan vérifié, deux relectures arbitrées par la session, une validation d’Isabelle, ticket réaligné), sans écrire de code ; parcours court pour un cadrage.
argument-hint: "[CLA-XX] [orchestre] [numéro d’ADR]"
disable-model-invocation: true
allowed-tools:
  - Bash(git branch --show-current)
---

# Planifier le ticket $0

Branche courante : !`git branch --show-current`

Tu es la session principale : tu orchestres, tu poses les questions métier, tu arbitres les relectures. Tu n’écris ni le plan ni le code.

Dans les noms de fichiers, `<id>` est `$0` en minuscules (`CLA-58` donne `cla-58`). Fichiers produits, hors git : `.claude/plans/<id>-context.md`, `.claude/plans/<id>-plan.md`, `.claude/plans/<id>-linear.md`, `.claude/plans/<id>-questions.md`, `.claude/plans/<id>-arbitrage.md`, et `.claude/plans/<id>-adr.md` (pour un cadrage).

Chaque sous-agent : outil Agent, `subagent_type: general-purpose`, avec le `model` indiqué à sa phase. Opus pour le rédacteur et les relecteurs, Sonnet pour le vérificateur de doc et l’intégrateur. Les briefs en fichier passent par leur chemin complet `${CLAUDE_SKILL_DIR}/…`. Attends la notification de fin d’un sous-agent avant d’utiliser son résultat ; ne résume jamais un résultat qui n’est pas revenu.

Si le titre du ticket commence par `[Cadrage]`, suis « Parcours court d’un cadrage » à la place des phases 1 à 4, avec ou sans orchestrateur.

## Lancé par l’orchestrateur

Seulement si `$1` vaut `orchestre` ; sinon, rien de cette section ne s’applique.

- Avant chaque attente d’Isabelle (question métier, validation unique ; cadrage : attente 1), passe `$0` en « Attente Isabelle » avec l’outil Linear de la session ; après sa réponse, remets-le en « In Progress ».
- La branche du ticket existe déjà et elle est extraite dans ce worktree : pas de `git switch develop` à l’étape 0 du plan.
- `$2` est le numéro d’ADR réservé : donne-le au rédacteur. Toute ADR de ce ticket prend ce numéro, et aucun autre.
- À la fin, après la publication du ticket réaligné (cadrage : en fin de parcours, après l’éventuel `<id>-linear.md`, voir « Parcours court d’un cadrage »), ajoute `plan_valide: AAAA-MM-JJ` à `.claude/plans/<id>-orchestration.md`, puis rends la main.

## Phase 1 — Questions (rédacteur)

1. Passe `$0` en « In Progress » avec l’outil Linear de la session, s’il est encore en Backlog ou Todo. Ce passage ne demande pas d’accord (voir `AGENTS.md`).
2. Lance le rédacteur (`model: opus`) : brief `${CLAUDE_SKILL_DIR}/writer.md`, phase « questions », identifiant `$0`.
3. Lis `<id>-questions.md`. Une question métier (`AGENTS.md`, « Échanges avec Isabelle ») est posée à Isabelle avant la suite, toutes d’un bloc de 10 lignes au plus, en tableau quand il y a plusieurs éléments. Les autres prennent la recommandation du rédacteur, marquée « à confirmer ». Sans question métier, aucune attente ici.

## Phase 2 — Contexte, puis plan (même rédacteur)

1. Reprends le **même** rédacteur avec SendMessage (outil différé : charge-le par ToolSearch) et donne-lui les réponses d’Isabelle et les défauts retenus : il rédige `<id>-context.md`.
2. Repli si SendMessage est indisponible : un rédacteur neuf reçoit le résumé du ticket, les questions, les réponses et les chemins des fichiers déjà écrits.
3. Le contexte n’est pas montré à part : il rejoint la validation unique (phase 4).
4. Phase « plan », dans un même message :
   - le même rédacteur, ou un neuf avec le même repli, rédige `<id>-plan.md` et marque « à vérifier » chaque version, option ou syntaxe d’outil qu’il affirme ;
   - un vérificateur de doc neuf (`model: sonnet`) reçoit la section « Brief du vérificateur de doc » ci-dessous, l’identifiant `$0` et le chemin du contexte.
5. Quand les deux sont revenus, transmets au rédacteur les constats du vérificateur, URL comprises. Si des marques « à vérifier » restent sans constat, relance d’abord le vérificateur sur cette liste. Le rédacteur finalise alors le plan sans refaire ces vérifications.

## Phase 3 — Deux relectures en parallèle (deux agents neufs)

1. Dans un même message, lance en arrière-plan :
   - `${CLAUDE_SKILL_DIR}/reviewers/technical.md` : justesse technique ;
   - `${CLAUDE_SKILL_DIR}/reviewers/fidelity.md` : fidélité et simplicité.
2. Ne leur donne que l’identifiant et les chemins, ni ton avis ni celui de l’autre.
3. Quand les deux sont revenus, tranche chaque correction. Retiens celles qui ont leur preuve ou suivent le contexte, écarte les autres avec leur raison. Écris le tableau (correction, relecteur, décision, raison) dans `.claude/plans/<id>-arbitrage.md`, section « plan ». Une correction qui change le besoin est une question métier : elle rejoint la validation unique.
4. Un intégrateur neuf (`model: sonnet`) reporte les décisions. Il reçoit la section « Brief de l’intégrateur » ci-dessous, la liste exacte de tes décisions et les chemins du plan, du contexte et de `<id>-linear.md` s’il existe déjà.

## Phase 4 — Ticket réaligné et validation unique (session)

Rédige `<id>-linear.md` au template de son type, aligné sur le contexte (règles ci-dessous). Puis **validation unique** : montre à Isabelle, d’un seul bloc de 10 lignes au plus, en tableau quand il y a plusieurs éléments, les défauts « à confirmer », les décisions d’arbitrage qui changent le plan, l’écart du ticket réaligné, et les chemins du contexte, du plan, de `<id>-arbitrage.md` (section « plan ») et de `<id>-linear.md`. Son accord explicite valide le contexte et le plan, et vaut accord pour publier `<id>-linear.md` (`AGENTS.md`). Remplis `validated:` du contexte à cette date. Une correction demandée passe par l’intégrateur, puis la publication suit sans nouvelle attente, sauf si Isabelle en demande une.

- Templates : `${CLAUDE_SKILL_DIR}/templates/` — `us.md` (fonctionnalité), `ts.md` (technique, outillage, dette), `bug.md` (anomalie), `cadrage.md` (question à trancher, sans code). Titre au préfixe du type : `US — …`, `TS — …`, `Bug — …`, `[Cadrage] … — …`.
- Toutes les sections du template restent, une ligne sans objet porte « aucune » ou « sans objet ».
- Les critères d’acceptation reprennent ceux du contexte, écrit puis validé avec le plan à la validation unique, en tableau `Étant donné | Quand | Alors`, cases d’état décochées. L’implémenteur n’écrit jamais dans Linear : `/implement-slice` coche l’état producteur après sa revérification, puis l’état testeur et la DOD après le « ok » d’Isabelle.
- La DOR est cochée à la publication du ticket réaligné, chaque case vérifiée sur le contexte et le plan validés.
- Priorité, estimation, labels et relations vont dans les champs Linear, pas dans la description.

## Parcours court d’un cadrage

Deux attentes d’Isabelle au plus sur tout le ticket, hors test de la PR : l’attente 1 ici, l’attente 2 dans `/implement-slice` (ADR 0022).

1. Passe `$0` en « In Progress », comme en phase 1.
2. **Attente 1.** Lance le rédacteur (`model: opus`) : brief `${CLAUDE_SKILL_DIR}/writer.md`, phase « questions cadrage », identifiant `$0`. Présente à Isabelle ses sources et toutes ses questions d’un seul bloc, et attends ses réponses. Une relance d’Isabelle ou une question de suite reste dans l’attente 1 : le ticket ne revient en « In Progress » qu’une fois toutes ses réponses données. Un point nouveau apparu ensuite devient un défaut « à confirmer » montré à l’attente 2, jamais une attente de plus. Le bloc montré tient en 10 lignes au plus, en tableau quand il y a plusieurs éléments, le détail dans `<id>-questions.md`.
3. En deux temps. D’abord le même rédacteur (SendMessage, repli de la phase 2), phase « cadrage », avec les réponses : il écrit `<id>-context.md` et `<id>-adr.md`, puis te rend la main.
   Ensuite, dans un même message :
   - le même rédacteur (SendMessage), phase « plan court » : il écrit `<id>-plan.md` ;
   - un vérificateur de doc neuf (`model: sonnet`) reçoit « Brief du vérificateur de doc, cadrage » ci-dessous, l’identifiant et le chemin de `<id>-adr.md`.
4. Transmets les constats du vérificateur au rédacteur, phase « finalisation cadrage » : il corrige l’ADR. Pas d’attente d’Isabelle ici ; garde les constats pour l’attente 2. Un point « introuvable » laisse la mention « À VÉRIFIER » dans le brouillon d’ADR : l’attente 2 le signale à Isabelle, et le fixup le traite avant la publication ; jamais d’ADR posé avec « À VÉRIFIER » au merge.
5. Ticket réaligné : si le ticket s’écarte du template `cadrage.md` ou de la décision prise, rédige `<id>-linear.md` comme en phase 4, sans le publier ; il rejoint l’attente 2. Sinon, aucun ticket réaligné.
6. Ni validation du contexte ou du plan, ni relecture de plan, ni arbitrage.
7. Fin : les trois fichiers écrits, l’ADR corrigé ; pose alors `plan_valide:` (après l’éventuel `<id>-linear.md`). L’implémentation se lance avec `/implement-slice $0`.

## Conditions d’arrêt

- Aucune branche, aucun commit, aucun fichier hors de `.claude/plans/` et du scratchpad.
- Rien dans Linear sans accord explicite d’Isabelle, sauf le passage en « In Progress » de la phase 1 et les statuts de « Lancé par l’orchestrateur ».
- Si la planification s’arrête sans plan validé, le signaler à Isabelle, qui décide du statut du ticket : aucun retour automatique.
- Fin : plan validé par Isabelle, ticket réaligné ; cadrage : contexte, plan court et ADR écrits, ADR corrigé. L’implémentation se lance avec `/implement-slice $0`.
- Règles du projet : `AGENTS.md`, « Règles pour tous les agents », « Échanges avec Isabelle » et « Conventions ».

## Brief du vérificateur de doc

> Tu vérifies les faits du contexte reçu, d’`AGENTS.md` et de la liste « à vérifier » si tu en reçois une. Un fait sur un outil (option, comportement, version) se vérifie dans sa documentation officielle, et seulement là. Un fait sur le projet se vérifie dans le ticket et dans les tickets qui lui sont directement liés, sans suivre leurs propres liens. Avant de répondre « introuvable », indiquer quelles sources ont été lues. Quand un fait est trouvé, citer sa source (URL de la doc ou identifiant du ticket). Tu lis Linear avec l’outil de la session, en lecture seule. Tu peux essayer une syntaxe sur une copie dans le scratchpad, jamais dans le dépôt.
>
> Interdits : aucune modification du dépôt, aucune écriture dans Linear.
>
> Retour, 20 lignes au plus. Pour chaque point : l’affirmation, « confirmé », « faux » ou « introuvable », la source (URL ou identifiant du ticket) et la date de lecture ; pour « introuvable », les sources lues.

## Brief du vérificateur de doc, cadrage

> Tu vérifies les sources du brouillon `.claude/plans/<id>-adr.md`. Pour chaque valeur ou règle chiffrée : la source citée existe, et elle dit ce que l’ADR lui fait dire. Tu lis les sources à leur adresse ; une page illisible (refus, 429) est « introuvable », avec l’adresse essayée. Tu lis Linear en lecture seule.
>
> Interdits : aucune modification du dépôt, aucune écriture dans Linear.
>
> Retour, 20 lignes au plus. Pour chaque valeur : la valeur, la source citée, « confirmé », « faux » ou « introuvable », l’extrait lu ou l’écart, et la date de lecture.

## Brief de l’intégrateur

> Tu reportes dans les fichiers reçus les décisions reçues, exactement, et rien d’autre : ni ajout, ni reformulation hors de ces décisions. Une décision ambiguë, ou qui contredit un autre passage : ne tranche pas, signale-la. Remplis `revised:` avec la date et l’origine des décisions (« arbitrages de la session » ou « corrections d’Isabelle »).
>
> Interdits : aucun fichier hors de ceux reçus, aucune branche, aucun commit, rien dans Linear.
>
> Retour, 10 lignes au plus :
> - pour chaque décision, le fichier et la section modifiés ;
> - les décisions non reportées, et pourquoi.
