# Cadrage

Titre : `[Cadrage] [sujet] — [question à trancher]`

|  |  |
| -- | -- |
| **Question à trancher** | \[une seule question, fermée si possible\] |
| **Pourquoi maintenant** | \[ce qui est bloqué tant qu’on n’a pas répondu\] |
| **Timebox** | \[1 à 5 jours\] · échéance JJ/MM |
| **Livrable** | Décision écrite (ADR ou note), liste de tickets à créer — jamais du code |
| **Sources à consulter** | \[documentation, essai dans un scratchpad, personne à interroger\] |

## Suites possibles

| Si la réponse est… | Alors on crée… |
| -- | -- |
| \[option A\] | \[US / TS pressenties\] |
| \[option B\] | \[fermeture du sujet, décision documentée\] |

## Critères d’acceptation

| \# | Étant donné | Quand | Alors | État producteur | État testeur |
| -- | -- | -- | -- | -- | -- |
| CA1 | la question à trancher | la timebox se termine | une décision écrite y répond, avec les options écartées et leur raison | - [ ] OK <br>- [ ] KO | - [ ] OK <br>- [ ] KO |
| CA2 | la décision prise | on lit « Suites possibles » | les tickets de la suite retenue sont listés, ou le sujet est fermé | - [ ] OK <br>- [ ] KO | - [ ] OK <br>- [ ] KO |
| CA3 | \[critère propre à la question\] | … | … | - [ ] OK <br>- [ ] KO | - [ ] OK <br>- [ ] KO |

## Hors périmètre

| Exclu | Pourquoi / où c’est traité |
| -- | -- |
| \[question voisine qu’on ne tranche pas ici\] | \[raison, ticket de renvoi\] |

## Références

|  |  |
| -- | -- |
| **Origine** | \[ticket, échange, constat\] |
| **Décision finale** | \[à compléter à la clôture : lien vers l’ADR ou la note\] |

| **DOR** | **DOD** |
| -- | -- |
| - [ ] La question est unique et formulée. | - [ ] La décision est écrite et liée dans « Décision finale ». |
| - [ ] La timebox est fixée. | - [ ] Chaque critère est coché en état producteur et en état testeur. |
| - [ ] Les sources à consulter sont listées. | - [ ] Les tickets de suite sont créés ou proposés. |
