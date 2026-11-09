@AGENTS.md

## Propre à Claude Code

- Les plans de ticket vivent dans `.claude/plans/`.
- `SendMessage` est un outil différé : le charger par ToolSearch avant l’appel.
- Fusionner les fixups sans éditeur : `GIT_SEQUENCE_EDITOR=: git rebase -i --autosquash origin/develop`.
- `git rev-parse --short` : une référence par appel.
