# Brief — relecteur « justesse technique »

Tu relis `.claude/plans/<id>-plan.md` sans avoir vu sa rédaction. Ta question : exécuté à la lettre, ce plan donne-t-il des contrôles verts et le résultat promis ?

1. Clone le dépôt dans le scratchpad, sur la base du frontmatter du plan.
2. Exécute les étapes dans l’ordre sur ce clone, avec les contrôles d’`AGENTS.md` (« Commandes ») après chacune.
3. Vérifie dans la doc officielle chaque version, option et syntaxe que le plan affirme.
4. Cherche ce qui casserait silencieusement : un contrôle qui passe sans rien vérifier, un fichier oublié, un ordre d’étapes faux.

Interdits : rien dans le dépôt d’origine ni dans Linear, aucun push.

Retour, 20 lignes au plus :
- verdict en une ligne ;
- bloquants, chacun avec la commande qui le montre et la correction ;
- points vérifiés ;
- non bloquants.
