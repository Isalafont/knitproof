# TS — Technical Story

Titre : `TS — [verbe technique + objet]`

|  |  |
| -- | -- |
| **Constat** | \[3 lignes max : dette, risque, outillage manquant, prérequis d’une US — factuel, sans solution\] |
| **Objectif technique** | \[état cible en une phrase\] |
| **Pourquoi maintenant** | \[US débloquée ou risque évité — sans réponse, la TS reste en Backlog\] |
| **Dépendances** | \[migration, outil, autre ticket\] ou « aucune » |

## Périmètre technique

| \# | Élément | Détail |
| -- | -- | -- |
| PT1 | \[module / fichier / outil touché\] | \[nature du changement\] |
| PT2 | \[migration de données ?\] | \[oui / non — réversibilité\] |
| PT3 | \[impact sur l’interface, l’API ou un autre dépôt ?\] | \[oui / non — lequel\] |

## Critères d’acceptation

| \# | Étant donné | Quand | Alors | État producteur | État testeur |
| -- | -- | -- | -- | -- | -- |
| CA1 | \[état initial\] | \[action ou commande\] | \[résultat vérifiable\] | - [ ] OK <br>- [ ] KO | - [ ] OK <br>- [ ] KO |
| CA2 | … | … | … | - [ ] OK <br>- [ ] KO | - [ ] OK <br>- [ ] KO |
| CA3 | \[non-régression : le comportement X reste inchangé\] | … | … | - [ ] OK <br>- [ ] KO | - [ ] OK <br>- [ ] KO |

## Hors périmètre

| Exclu | Pourquoi / où c’est traité |
| -- | -- |
| \[ce qu’on ne fait pas\] | \[raison, ticket de renvoi\] |

## Références

|  |  |
| -- | -- |
| **Tickets liés** | \[CLA-xx\] ou « aucun » |
| **Plan / décisions** | \[`.claude/plans/…`, ADR, PR ou incident\] |

| **DOR** | **DOD** |
| -- | -- |
| - [ ] Le constat et le « pourquoi maintenant » sont écrits. | - [ ] Les cinq contrôles d’`AGENTS.md` sont verts. |
| - [ ] Les critères sont vérifiables, sans ambiguïté. | - [ ] Chaque critère est coché en état producteur et en état testeur. |
| - [ ] Les dépendances sont levées ou sécurisées. | - [ ] README et doc sont à jour. |
| - [ ] Le ticket est estimé. | - [ ] Une ADR dans `docs/adr/` consigne toute décision structurante. |
