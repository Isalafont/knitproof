# Commandes et développement

Détail des commandes de knitproof, de l’organisation du code et de la contribution. Le README en donne l’essentiel.

## Organisation du code

`domain` et `engine` portent le modèle de patron, le calcul du bonnet et la vérification des comptes de mailles ; `app` et `cli` portent les commandes `knitproof calc` et `knitproof verify` ; les autres paquets de `src/knitproof/` sont vides pour l’instant. Ils fixent les contrats de couches, que `uv run lint-imports` vérifie. Les deux exemples de la section « Ce que ça donne » vivent dans `examples/` ; leurs sorties de référence vivent dans `examples/sorties/` et un test garde les blocs du README contre elles (balise `<!-- sortie : … -->` avant chaque bloc). Les patrons synthétiques justes vivent dans `examples/synthetiques/`, et la CI les vérifie tous.

## Données Ravelry

Pour les données Ravelry, copier `.env.example` en `.env` et y renseigner ses identifiants d’API. Le fichier `.env` n’est jamais versionné.

## Calculer un bonnet

La commande `knitproof calc` lit une demande YAML (format décrit dans [`docs/architecture.md`](architecture.md), section 9), applique l’aisance, calcule le plan du bonnet, contrôle le montage proposé et les aiguilles, puis rend un rapport unique sur stdout.

```sh
uv run knitproof calc examples/bonnet-3-ans.yaml
```

Le code de sortie dit le résultat, et ne se lit pas comme celui de `verify` :

- `0` : un plan est calculé, avec ou sans alerte ou rejet dans le rapport ;
- `1` : des questions restent en attente (par exemple, pas de jauge en rangs, ou un échantillon d’état de blocage inconnu), pas de plan ; les questions sortent sur stdout ;
- `2` : erreur d’usage (fichier non précisé), message sur stderr ;
- `3` : fichier absent, illisible ou invalide (clé inconnue, nombre trop grand), message sur stderr, sans trace Python.

Pour `verify`, `1` veut dire « au moins un constat ».

Les tailles d’aiguilles s’écrivent « 4 mm », « US 6 » ou « US 6 (4 mm) » ; le texte rendu garde la notation saisie et donne les mm de la table, « À VÉRIFIER » sur l’emballage. L’âge, le fil et la fibre ne sont pas lus : leur résolution revient à un ticket de suite et à CLA-121. La jauge se résout : échantillon bloqué, puis non bloqué (« À VÉRIFIER »), puis étiquette (`label_gauge`, « À VÉRIFIER ») ; un échantillon d’état de blocage inconnu (`unknown_blocking`) pose la question « l’as-tu bloqué ? » et la réponse se donne en renommant la clé.

## Vérifier un patron YAML

La commande `knitproof verify` vérifie les comptes de mailles d’un fichier au format décrit dans [`docs/architecture.md`](architecture.md), section 9. Un patron réel se range dans `local-patterns/`, que git ignore : il ne quitte pas votre machine et aucun test de la CI ne le lit.

```sh
uv run knitproof verify local-patterns/mon-bonnet.yaml
```

Le rapport sort sur stdout. Le code de sortie dit le résultat :

- `0` : aucun constat ;
- `1` : au moins un constat, rapporté sur stdout ;
- `2` : erreur d’usage (par exemple, fichier non précisé), message sur stderr ;
- `3` : fichier absent, illisible ou invalide, message sur stderr, sans trace Python.

Les comptes (`cast_on`, `work`, `times`, `start`, `end`, `stated_count`) sont des entiers nus : une chaîne, un nombre à virgule ou un booléen rend le patron invalide (code 3).

Pour vérifier plusieurs fichiers d’un coup, un test à la demande lit ceux que désigne `KNITPROOF_PATTERNS`. Depuis la racine du dépôt, un fichier, puis tous ceux d’un dossier (motif glob, entre apostrophes pour que le shell ne le développe pas) :

```sh
KNITPROOF_PATTERNS=local-patterns/mon-bonnet.yaml uv run pytest tests/test_pattern_files.py
KNITPROOF_PATTERNS='local-patterns/*.yaml' uv run pytest tests/test_pattern_files.py
```

Lire le résultat :

- `1 passed` : aucun constat, chaque compte annoncé est celui que calcule le moteur.
- `1 failed` : une ligne par constat, le fichier, puis le même bloc que `knitproof verify`, avec le rang. Par exemple, sur `examples/bonnet-erreur-rang-33.yaml` : `Rang 33 — nombre de mailles incohérent`, puis `Annoncé : 89 m · Calculé : 90 m`. Pour un `repeat_not_fitting`, le bloc donne les mailles laissées par le rang précédent et celles que consomment les opérations ; la simulation s’arrête à ce rang.
- Un motif qui ne trouve aucun fichier, ou un fichier invalide (opération inconnue, clé en trop), échoue avec la raison.
- Sans la variable, le test est sauté (`1 skipped`) : `uv run pytest` ne lit jamais `local-patterns/`. Préfixer la commande, ne pas exporter la variable.

Limites :

- Seules `work`, `k2tog`, `m1` et `repeat` sont prises en charge ; les diminutions des patrons synthétiques sont toutes écrites en `k2tog`. Un fichier qui emploie une autre opération est rejeté, et ce rejet ne prouve pas une erreur de calcul.
- Le multiple du point (côtes 2/2…) n’est pas vérifié : la commande et le test comptent les mailles, ils ne contrôlent pas le montage. `knitproof calc` calcule et contrôle le montage d’un seul point (multiple et reste saisi), au plus proche, en dessous en cas d’égalité ; `knitproof verify` ne le vérifie pas. Le rang d’ajustement entre bord et corps (ADR 0025) n’est exposé par aucune commande.
- Les tailles d’aiguilles de deux systèmes (US, UK, japonais, mm) ne sont pas converties : le moteur avertit qu’il ne peut pas les comparer, sauf si leur taille en mm est connue des deux côtés (écrite en mm, ou saisie à côté d’une autre notation). `knitproof calc` signale la différence entre l’échantillon et le projet (`swatch_needle_mismatch`) ; `verify` ne compare pas les aiguilles.
- Après un `repeat_not_fitting`, les comptes annoncés suivants ne sont pas comparés ([ADR 0013](adr/0013-format-yaml-fige-et-poursuite-sur-le-compte-calcule.md)).
- Seuls les comptes de mailles sont vérifiés : ni mesures, ni échantillon.

Les patrons synthétiques justes de `examples/synthetiques/` sont vérifiés par la CI à chaque `uv run pytest`, sans variable.

## Contribuer

- GitHub supprime la branche distante au merge ; en local, `git fetch -p` puis `git branch -d <branche>` (sans worktree ouvert : `git fetch -p` déplace les références distantes partagées et annule le lease des worktrees).
- ruff vérifie aussi le nommage (`N`), le style pytest (`PT`), ses propres règles (`RUF`) et les nombres magiques dans `src/` (`PLR2004`) ; l’apostrophe typographique et les espaces insécables sont permis. mypy refuse `Any` ([ADR 0012](adr/0012-interdire-any-avec-mypy.md)). Les conventions que les outils ne vérifient pas sont dans `AGENTS.md`.
