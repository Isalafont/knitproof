# ADR 0031 — Aisance d’après les patrons et la laine

Amende l’[ADR 0024](0024-aisance-du-bonnet.md) (points 3 et 5) ; nuance l’[ADR 0030](0030-laines-de-reference.md).

## Contexte

Une source par couple (ajustement, point) laisse sans valeur le bonnet ajusté en côtes 2/2, le plus courant. Les patrons DROPS relus chez le fabricant en donnent plusieurs. La laine et le point de l’échantillon changent la lecture d’un patron. Données brutes : `src/knitproof/library/data/0031-*.yaml`.

## Décision

Décisions d’Isabelle du 12/11/2026 (`person_decision`).

1. **Plusieurs sources par couple** : valeur proposée = médiane des médianes par patron, plage = plus faible et plus forte de ces médianes ; la plage par taille est rendue à part.
2. **Un patron compte** s’il correspond à l’ajustement, au point du bord, au point de l’échantillon et à la famille de la laine (`Yarn.family` : fibre majoritaire et superwash ; égalité de parts ou superwash inconnu : pas de famille, donc pas de correspondance). Une source sans laine nommée vaut pour toute laine, une source sans échantillon pour tout point (à confirmer).
3. **Point de l’échantillon** : « Si l’utilisateur donne un échantillon directement en côtes et que tout le bonnet est fait en côtes, on prend en compte son échantillon. » Un échantillon en côtes sans source au même point : aucune valeur, repères rendus.
4. **Base de −5 %** pour un bonnet ajusté à bord en côtes (1/1 ou 2/2) et échantillon en jersey, quand aucune source ne correspond ; « À VÉRIFIER ». Manques : coton, aucune valeur proposée ; (ample, côtes 2/2), le Rosebud reste la seule source.
5. **Repères** (`landmark`) : montrés, jamais comptés, avec leur raison. DROPS Air (214-67, 219-17), 242-22, 260-24, Purl Soho, Barley, Simple Baby Hat et Tegan : côtes 1/1, bord roulotté ou au point mousse, mailles du corps, ou laine non relue.
6. **Jamais de pourcentage demandé** : « Une tricoteuse ne saura pas te donner une aisance en pourcentage. » Deux réponses au choix : « Certaines sauront te dire 5 ou 10 cm de moins que le tour de tête et d’autres mesureront par un bonnet qu’elles aiment et te donneront ces mesures-là. » Les questions vont au ticket de suite.
7. **Prématurés** : « Jamais proposer d’aisance sur les prématurés, il faut que ça soit confortable et pas trop serré. » Les tailles de prématurés (Tegan « Premature / Small Newborn », Simple Baby Hat « Preemie ») n’entrent pas dans les sources ; la règle dans `knitproof calc` relève du ticket de suite.

| Ajustement | Bord | Échantillon | Laine | Valeur proposée | Plage des médianes |
|---|---|---|---|---|---|
| ajusté | côtes 2/2 | jersey | mérinos superwash | −4,8 % (trois patrons DROPS) | −7,4 à −3,7 % (par taille : −8,95 à +2,98 %) |
| ajusté | côtes 1/1 ou 2/2 | jersey | autre | −5 % (base) | repères |
| ajusté | côtes | côtes | toute | aucune | repères |

## Alternatives écartées

- **Constante −5 % dans le moteur** : un nombre sans source est interdit ; la base est une donnée.
- **Tout dans le fichier de l’ADR 0024** : `decided_in` serait faux pour les ajouts.
- **Tous les patrons dans la valeur** : un tour du corps ou un bord roulotté n’est pas un bord en côtes.

## Conséquences

- Le moteur lit la fibre et le superwash de la laine pour l’aisance seulement, la détente restant mesurée par l’échantillon (ADR 0030) ; le branchement dans `knitproof calc` revient au ticket de suite.

## Sources

- Décisions d’Isabelle, 12/11/2026 ; patrons relus le 12/11/2026, adresses citées dans le YAML.
