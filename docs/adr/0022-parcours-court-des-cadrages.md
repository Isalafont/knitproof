# ADR 0022 — Parcours court des cadrages

## Contexte

Le premier usage de `/orchestrate`, le 02/11/2026, a compté 31 passages en « Attente Isabelle » pour 4 cadrages (CLA-78 à CLA-81), et 338 à 521 lignes de contexte et de plan pour 65 à 139 lignes livrées (bilan du 02/11/2026 sur CLA-111). Les cadrages suivaient le parcours conçu pour du code.

## Décision

1. Un ticket dont le titre commence par `[Cadrage]` suit un parcours court, avec ou sans orchestrateur.
2. Isabelle n’attend que deux fois, hors test de la PR : d’abord sources et questions, d’un bloc ; puis, avant la PR, l’ADR, les constats du vérificateur et de la relecture, les cases producteur, le ticket réaligné s’il s’écarte du template ou de la décision, la DOR, les tickets de suite et leur publication.
3. Après la première attente, le rédacteur écrit le contexte, un plan court (fichiers, lignes, commits) et le brouillon d’ADR. Le plan court n’est ni validé ni relu.
4. Un vérificateur de doc contrôle que chaque source citée par le brouillon d’ADR existe et dit ce qu’on lui fait dire. Le rédacteur corrige l’ADR sur ses constats, sans attente.
5. L’implémenteur pose le brouillon d’ADR sans le réécrire. Une seule relecture du diff.
6. Le « ok » d’Isabelle sur le test vaut accord pour publier les cases testeur et la DOD.
7. `/orchestrate` compte les cadrages dans `--max N`, 2 au plus à la fois.

## Alternatives écartées

- Aucun plan : `/implement-slice` aurait perdu son contrat « exécute le plan ».
- Rédaction de l’ADR par l’implémenteur : il n’a pas lu les sources.
- Aucune vérification des sources : la relecture du diff ne les rouvre pas toutes.
- Quota de cadrages séparé de `--max N` : deux limites à suivre au lieu d’une.
- Alléger aussi les tickets de code : à décider après l’essai sur les cadrages.

## Conséquences

- Isabelle ne valide plus le contexte d’un cadrage à part : ses réponses de la première attente le fixent.
- Le test de la PR et le « ok » d’Isabelle restent le garde-fou avant le merge.
- L’essai se mesure sur CLA-77, CLA-82 et CLA-113 : moins de 3 passages en « Attente Isabelle » par ticket.
