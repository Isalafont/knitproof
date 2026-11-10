# US — User Story

Titre : `US — [verbe + objet + pour qui]`

|  |  |
| -- | -- |
| **Description** | **En tant que** \[rôle précis\], **je veux** \[action\], **afin de** \[bénéfice\]. |
| **Constat** | \[3 lignes max : le problème vécu aujourd’hui, factuel, sans solution\] |
| **Utilisateurs concernés** | \[qui est impacté\] |
| **Valeur** | \[ce que ça change concrètement\] |
| **Dépendances** | \[autre ticket, décision, donnée\] ou « aucune » |

## Proposition technique

\[Approche et fichiers clés, en bref. Points d’attention : accessibilité RGAA 4.1 AA, sécurité, données.\]

## Règles de gestion

| \# | Règle | État producteur | État testeur |
| -- | -- | -- | -- |
| RG1 | \[règle de comportement / d’affichage\] | - [ ] OK <br>- [ ] KO | - [ ] OK <br>- [ ] KO |
| RG2 | \[invariant : ce qui ne change jamais\] | - [ ] OK <br>- [ ] KO | - [ ] OK <br>- [ ] KO |
| RG3 | \[cas limite : que se passe-t-il si…\] | - [ ] OK <br>- [ ] KO | - [ ] OK <br>- [ ] KO |

## Critères d’acceptation

| \# | Étant donné | Quand | Alors | État + RG producteur | État testeur |
| -- | -- | -- | -- | -- | -- |
| CA1 | \[état initial\] | \[action\] | \[résultat vérifiable\] | - [ ] OK <br>- [ ] KO<br><br>RG1 | - [ ] OK <br>- [ ] KO |
| CA2 | \[cas nominal secondaire\] | … | … | - [ ] OK <br>- [ ] KO<br><br>RG… | - [ ] OK <br>- [ ] KO |
| CA3 | \[cas d’erreur\] | … | … | - [ ] OK <br>- [ ] KO<br><br>RG… | - [ ] OK <br>- [ ] KO |
| CA4 | \[accessibilité, si interface : clavier, lecteur d’écran, contrastes\] | … | … | - [ ] OK <br>- [ ] KO | - [ ] OK <br>- [ ] KO |
| CA5 | \[non-régression : le parcours X reste inchangé\] | … | … | - [ ] OK <br>- [ ] KO | - [ ] OK <br>- [ ] KO |

## Hors périmètre

| Exclu | Pourquoi / où c’est traité |
| -- | -- |
| \[ce qu’on ne fait pas\] | \[raison, ticket de renvoi\] |

## Références

|  |  |
| -- | -- |
| **Tickets liés** | \[CLA-xx\] ou « aucun » |
| **Plan / décisions** | \[`.claude/plans/…`, ADR\] |

| **DOR** | **DOD** |
| -- | -- |
| - [ ] Le constat et la valeur sont écrits : on sait pourquoi on le fait. | - [ ] Les cinq contrôles d’`AGENTS.md` sont verts. |
| - [ ] Les critères sont vérifiables, sans ambiguïté. | - [ ] Chaque critère est coché en état producteur et en état testeur. |
| - [ ] Les dépendances sont levées ou sécurisées. | - [ ] README et doc sont à jour. |
| - [ ] Le ticket est estimé. | - [ ] Une ADR dans `docs/adr/` consigne toute décision structurante. |
