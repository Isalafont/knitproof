# Bug

Titre : `Bug — [symptôme observé + où]`

|  |  |
| -- | -- |
| **Comportement observé** | \[ce qui se passe, message d’erreur exact si affiché\] |
| **Comportement attendu** | \[ce qui devrait se passer\] |
| **Impact** | \[ce qui est bloqué, contournement existant ?\] |
| **Environnement** | \[local / déployé — version, commit, système\] |

## Étapes de reproduction

| \# | Étape | Résultat |
| -- | -- | -- |
| 1 | \[action ou commande\] | \[observé\] |
| 2 | \[action ou commande\] | \[observé\] |
| 3 | \[action ou commande\] | \[le bug\] |

## Pièces jointes

\[captures d’écran, logs, trace d’erreur\]

## Critères d’acceptation

| \# | Étant donné | Quand | Alors | État producteur | État testeur |
| -- | -- | -- | -- | -- | -- |
| CA1 | \[état initial de la reproduction\] | \[étape qui déclenche le bug\] | \[comportement attendu\] | - [ ] OK <br>- [ ] KO | - [ ] OK <br>- [ ] KO |
| CA2 | \[le correctif\] | \[la suite de tests tourne\] | \[un test reproduit le bug et passe\] | - [ ] OK <br>- [ ] KO | - [ ] OK <br>- [ ] KO |
| CA3 | \[non-régression : le comportement X reste inchangé\] | … | … | - [ ] OK <br>- [ ] KO | - [ ] OK <br>- [ ] KO |

## Hors périmètre

| Exclu | Pourquoi / où c’est traité |
| -- | -- |
| \[ce qu’on ne corrige pas ici\] | \[raison, ticket de renvoi\] |

## Références

|  |  |
| -- | -- |
| **Tickets liés** | \[CLA-xx, ticket ayant introduit le bug\] ou « aucun » |
| **PR / commit en cause** | \[lien le cas échéant\] |

| **DOR** | **DOD** |
| -- | -- |
| - [ ] Le bug est reproductible avec les étapes ci-dessus. | - [ ] Les cinq contrôles d’`AGENTS.md` sont verts. |
| - [ ] Le comportement attendu est écrit. | - [ ] Chaque critère est coché en état producteur et en état testeur. |
| - [ ] Le ticket est estimé. | - [ ] README et doc sont à jour si le comportement documenté change. |
