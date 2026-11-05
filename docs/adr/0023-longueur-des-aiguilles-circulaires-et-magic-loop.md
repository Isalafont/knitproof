# ADR 0023 — Longueur des aiguilles circulaires et passage en magic loop

Complète l’[ADR 0016](0016-tailles-d-aiguilles-sans-conversion.md) et l’[ADR 0019](0019-calotte-du-bonnet.md), qui restent inchangées.

## Contexte

La question tricot 12 demande deux choses : quelle longueur d’aiguille circulaire convient à une circonférence donnée, et à quel rang de la calotte passer aux doubles pointes ou au magic loop. CLA-68 en a besoin pour son constat `needle_change` (RG2, CA2). `docs/architecture.md` dit seulement qu’« un câble de circulaire trop long pour la circonférence du tricot ne permet pas de tricoter ».

`Needle.cable_length` est facultatif pour `circular` et refusé pour `straight` et `double_pointed` (ADR 0016). Son sens n’est pas fixé : longueur du câble seul, ou longueur totale de l’aiguille.

Les fabricants ne mesurent pas tous de la même façon :

- **addi** : la longueur d’un câble addiClick « correspond toujours à la longueur totale des deux pointes et du câble », comme pour une circulaire fixe. Les pointes mesurent environ 125 mm (longues) ou 90 mm (courtes). Un câble de 60 cm mesure environ 35 cm seul. Source : https://addi.de/en/c/knitting/addiclick-needle-sets/zubehoer-addiclick/
- **KnitPro** : la longueur est mesurée de pointe à pointe, « selon l’usage standard de l’industrie », une fois les pointes montées. Le câble de 40 cm est prévu pour les « shorter interchangeable needles only » : avec d’autres pointes, il ne donne pas 40 cm. Source : https://www.woolwarehouse.co.uk/knitpro-interchangeable-circular-knitting-needle-cables-black-plastic. Pointes « normal and special » de 13 et 10 cm : https://www.knitpro.eu/usa/zing-interchangeable-circular-needles
- **ChiaoGoo TWIST** : la longueur annoncée est celle du câble seul : « actual cable length », https://www.chiaogoo.com/faqs/. Un câble de 14″ (35 cm) fait une circulaire de 24″ (60 cm) avec des pointes de 5″ (13 cm). Un câble de 8″ (20 cm) fait une circulaire de 16″ (40 cm) avec des pointes de 4″ (10 cm). Source : https://www.yarn.com/products/chiaogoo-twist-red-cable-small. Pointes de 3″, 4″ et 5″ (8, 10 et 13 cm) : « All of our 3″ (8cm), 4″ (10cm) and 5″ (13cm) tips », https://www.chiaogoo.com/faqs/.

Ce que disent les guides :

- La longueur d’une circulaire se mesure de pointe à pointe. Une aiguille ne doit pas être plus longue que la circonférence du tube tricoté, et la circonférence vaut mailles / jauge (la page l’appelle « diameter », mais la calcule et l’emploie comme la circonférence). Donna Jones Designs : https://crimson-triangle-6gsk.squarespace.com/blog/2015/08/31/length-circular-needles-use
- La circulaire doit être plus courte que la circonférence. Un 16″ va pour un bonnet adulte de 18 à 22″, un 24″ est trop long. Aucun seuil de passage aux doubles pointes n’est donné. Elizabeth Smith : https://elizabethsmithknits.com/2024/01/19/the-basics-of-circular-needle-lengths/
- Le magic loop demande « at least 32 inches (81 cm) » dans le corps de la page, « 32 inches (80 cm) » dans son introduction. KnitPro : https://www.knitpro.eu/en/blog/knit-the-magic-loop-on-circular-needles. Il « can be performed on our 32″ cable or anything longer », et certains clients disent avoir réussi sur 24″, ce qui nuance le minimum. Knit Picks : https://tutorials.knitpicks.com/magic-loop/
- Oslo (PetiteKnit) : corps sur circulaire de 40 cm, calotte « on DPNs or on a longer circular needle using the Magic Loop technique », sans seuil chiffré. Fiche revendeur : https://loopknitting.com/products/petiteknit-oslo-hat
- Jakob Wolle : la longueur annoncée n’est « nicht das Seil selber, sondern die Gesamtlänge von Seil und Nadelspitzen », ce qui appuie la règle de longueur totale. Sa table de mailles, « gerechnet auf 2.5 cm », n’est pas retenue (voir les alternatives) : https://www.jakob-wolle.ch/upload/cms/PDF/Tipps%20Auswahl%20der%20richtigen%20Nadeln%20NEU.pdf

## Décision

Décisions d’Isabelle du 05/11/2026.

1. **Règle de longueur.** On compare à la circonférence la longueur totale de l’aiguille circulaire, de pointe à pointe, pointes comprises. Le câble seul ne suffit pas. Une circulaire tricote en rond sans magic loop si `longueur totale ≤ circonférence`. L’égalité est admise, comme le « pas plus longue » de Donna Jones ; Elizabeth Smith écrit « plus courte ». La règle vient de l’avis d’Isabelle, de Donna Jones et d’Elizabeth Smith ; la convention de pointe à pointe vient d’addi, KnitPro et Jakob Wolle. Exemple d’Isabelle : un câble de 40 cm avec des pointes de 10 cm fait 60 cm et ne permet pas de tricoter un bonnet de 40 cm.
2. **Doubles pointes.** La règle de longueur ne s’applique pas : les mailles sont réparties sur 3, 4 ou 5 aiguilles (avis d’Isabelle). Avec des doubles pointes, le moteur n’émet aucun `needle_change` ni `warning` de longueur.
3. **Circonférence sur l’aiguille.** Circonférence = mailles × largeur de l’échantillon / mailles de l’échantillon. Elle se calcule avec la jauge avant blocage si elle est connue, puisque le tricot sur l’aiguille n’est pas encore lavé. Sinon, la jauge après blocage sert, et le constat est marqué « À VÉRIFIER : jauge après blocage, le tricot sur l’aiguille peut être plus étroit ». La comparaison se fait par produit croisé exact, `longueur × mailles de l’échantillon ≤ mailles × largeur de l’échantillon`, longueurs dans la même unité, sans quotient (ADR 0015).
4. **Passage dans la calotte (`needle_change`).** Pour une circulaire de longueur connue, le constat porte sur le premier rang de la calotte qui commence avec un compte dont la circonférence est inférieure à la longueur totale. Le moteur ne calcule que ce rang de passage. Le texte propose le magic loop sur câble long ou les doubles pointes, sans choisir. Une circulaire déjà trop longue pour le corps (point 5) ne donne pas de `needle_change`.
5. **Aiguille trop longue dès le montage.** Si la longueur totale dépasse la circonférence du corps, le moteur émet un `warning` et non un refus. Le texte propose le magic loop sur câble long, une circulaire plus courte ou des doubles pointes. Le magic loop permet de tricoter quand même. Ce constat remplace alors le `needle_change` de la calotte.
6. **Magic loop.** Le câble doit permettre de faire deux boucles (avis d’Isabelle). 80 cm est un ordre de grandeur, donné en conseil et non calculé, avec sa source : expérience des tricoteuses selon Isabelle, KnitPro « at least 32 inches (81 cm) » (80 cm dans son introduction), Knit Picks « 32″ cable or anything longer », nuancé par des essais réussis sur 24″. Le moteur ne vérifie pas qu’un câble saisi permet deux boucles : aucune source ne donne de règle calculable.
7. **Circulaire sans longueur saisie.** Pas de rang calculé. Le moteur conseille, à l’entrée de la calotte, de passer en magic loop sur câble long, ou aux doubles pointes, « quand le tricot se tend sur l’aiguille » (avis d’Isabelle).
8. **Convention de saisie.** `cable_length` vaut la longueur totale de l’aiguille, de pointe à pointe, comme l’annoncent addi, KnitPro et les circulaires fixes ; la doc le dit. Pour une aiguille ChiaoGoo TWIST, dont la longueur annoncée est celle du câble seul, la personne saisit câble + deux pointes. Saisir le câble et les pointes à part est écarté : un seul champ suffit, et `Needle` ne change pas.

### Exemple

D’après `examples/bonnet-3-ans.yaml` : 22 m/10 cm avant blocage, 20 m/10 cm après. Montage calculé de 88 m (README), circulaire fixe de 40 cm de pointe à pointe supposée. Comptes de la calotte selon l’ADR 0019.

| Jauge | Corps (88 m) | Premier rang sous 40 cm | `needle_change` |
|---|---|---|---|
| 22 m (avant blocage) | 40,0 cm, passe (égalité admise, point 1) | 80 m : 36,4 cm | rang 2 de la calotte |
| 20 m (après blocage, « À VÉRIFIER ») | 44,0 cm, passe | 72 m : 36,0 cm | rang 4 de la calotte |

Avec un câble ChiaoGoo de 40 cm et des pointes de 10 cm, soit 60 cm au total, le corps de 40 ou 44 cm donne le `warning` du point 5 dès le montage.

## Alternatives écartées

- Câble seul comparé à la circonférence : faux dès que les pointes sont longues (correction d’Isabelle du 05/11/2026).
- Longueur × coefficient (aiguille « un peu plus courte ») : aucune source ne chiffre la marge.
- Table de mailles de Jakob Wolle (en 5 mm : 80, 120, 150, 210 et 250 m pour 40, 60, 80, 100 et 120 cm) : elle ne couvre que de 5 à 9 mm, et rien ne dit s’il s’agit d’un minimum ou d’un maximum.
- Passage toujours à l’entrée de la calotte : l’Oslo ne fixe pas de seuil, et cette option ignore la longueur saisie, alors que le moteur peut la comparer.
- Conseil seul, sans calcul, même quand la longueur est connue : retenu seulement en repli (point 7).
- Refus ou `needs_review` quand l’aiguille est trop longue au montage : le magic loop permet de tricoter.
- Longueur minimale du magic loop vérifiée par le moteur : la règle des deux boucles n’est pas calculable avec une source.
- Choisir entre doubles pointes et magic loop : affaire de préférence, aucune source ne tranche.
- Saisir le câble et les pointes à part : un seul champ suffit avec la longueur de pointe à pointe, sans changer `Needle` (ADR 0016).

## Conséquences

- CLA-68 applique les points 1 à 7 : il reformule sa RG2 et son CA2 avec la longueur totale de l’aiguille, et teste l’exemple ci-dessus. La comparaison se teste par produit croisé, sur les deux jauges.
- `docs/architecture.md` l. 190 : sens de `cable_length` selon le point 8. L. 255 : règle de longueur totale, `needle_change` et `warning`.
- `docs/plan.md` : question 12 tranchée.
- Ticket de suite proposé, sans identifiant tant qu’il n’est pas créé : « recommander une longueur de circulaire » d’après la circonférence du corps et les longueurs vendues par les fabricants, à sourcer.
- Aucun ticket sur `Needle` : seule la doc change (point 8).
