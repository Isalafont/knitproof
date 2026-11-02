# ADR 0017 — Worktrees et force-with-lease

## Contexte

Plusieurs tickets sont démarrables en parallèle, mais le dépôt n’a qu’un checkout et `--force-with-lease` est interdit : un ticket rebasé ne peut pas être repoussé.

## Décision

1. Chaque ticket orchestré a son worktree frère `../knitproof-<id>`, créé par `git worktree add --no-track` depuis `origin/develop`, sur la branche du ticket Linear.
2. `.claude/plans/` y est un lien symbolique vers le checkout principal : les plans sont partagés.
3. `git push --force-with-lease origin feature/*` est permis, sur `feature/*` seulement. `--force`, `-f` et `+<réf>` restent refusés. Seules `develop` et `main` sont contrôlées comme cibles par les règles : une refspec vers un autre nom (`feature/x:autre`) n’est pas refusée.
4. En worktree, une branche se rebase juste avant le test de la PR, puis avant le merge, si `develop` a avancé. Sans conflit et CI reverte, le « ok » d’Isabelle tient ; conflit résolu, nouveau « ok ».
5. Le numéro d’ADR est réservé au lancement du ticket ; un trou dans la numérotation est accepté.
6. Le statut Linear « Attente Isabelle » marque une attente de validation hors test de la PR, pour les skills lancés par l’orchestrateur seulement.

## Alternatives écartées

- Emplacement `.claude/worktrees/<id>` : les `CLAUDE.md` parents seraient concaténés.
- `claude --worktree` : branche `worktree-<nom>`, base par défaut, écritures vers le principal bloquées.
- `herdr worktree create` : ouvre un workspace à part au lieu d’une pane.
- Copie des plans (`.worktreeinclude`) : une copie n’est pas partagée.
- `--force-if-includes` ou `--force-with-lease=<branche>:<sha>` : règles et essais en plus, ou refus par le deny.
- Signal entre panes par statut Linear : il ne dit pas « plan validé » ni « merge fait » de façon sûre.
- Test pytest relisant `settings.json` : ne prouve rien du moteur de permissions.
- Multica : écarté au profit de herdr, déjà en place.

## Conséquences

- Isabelle reste le goulot : chaque ticket occupe sa place jusqu’au merge.
- La relecture du diff n’est pas refaite après un rebase.
- Les règles `Bash` ne sont pas une frontière de sécurité (doc des permissions) et ne remplacent pas les rulesets GitHub.
- Dans un worktree, on ne récupère que `develop` (`git fetch origin develop`) : un `git fetch origin` déplacerait `origin/<branche>` et annulerait la protection du lease.
