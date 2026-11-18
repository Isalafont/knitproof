# Design de l’interface

Choix visuels et éditoriaux de l’interface web (M3, étape 2 du [plan](plan.md)), arrêtés le 18/11/2026 sur une maquette : accueil, calcul et vérification, en français et en anglais, sur ordinateur, téléphone et tablette. Tickets : [CLA-209](https://linear.app/claude-personnal/issue/CLA-209) (calcul), [CLA-210](https://linear.app/claude-personnal/issue/CLA-210) (vérification), [CLA-211](https://linear.app/claude-personnal/issue/CLA-211) (mode tricot).

Maquette : [knitproof, FR et EN](https://claude.ai/artifact/AGDxtgx7ersmiPunr61oKb) (privée tant qu’elle n’est pas partagée).

## Mobile d’abord

Les tricoteuses utilisent surtout leur téléphone ou leur tablette, souvent en tricotant ; seules les créatrices de patrons travaillent sur ordinateur. L’interface se conçoit d’abord à 390 px, puis pour la tablette et l’ordinateur.

| Écran | Téléphone | Tablette |
|---|---|---|
| En-tête | logo, bouton de langue, bouton « Menu » | logo, menu court, langue |
| Formulaire de calcul | une étape par écran (« Étape 2 sur 4 », barre d’avancement), boutons « Précédent » et « Suivant » en bas | comme l’ordinateur |
| Résultat du calcul | montage en tête, puis mode tricot ; origine des chiffres repliée | mode tricot à gauche, montage, doute et origine à droite |
| Résultat de la vérification | l’écart en tête, « Annoncé / Compté » côte à côte, le tableau devient une liste | comme l’ordinateur |

Boutons pleine largeur et d’au moins 52 px de haut pour les actions principales ; aucun défilement horizontal à 320 px de large ni à 200 % de zoom.

## Publics

| Support | Pour qui | Ton |
|---|---|---|
| Interface web | tricoteuses, d’abord | simple, sans jargon technique ; un trait d’humour bienvenu |
| README, `docs/` | développeurs, recruteurs | ingénierie : moteur déterministe, provenance, évaluation |

Dans l’interface, on évite « moteur », « provenance », « prouvé », « LLM », « aisance négative ». On dit « knitproof calcule », « vous savez d’où vient un chiffre », « bonnet plus serré que la tête ».

L’interface ne promet pas la gratuité : un produit payant est envisagé avec les pulls ([CLA-83](https://linear.app/claude-personnal/issue/CLA-83)).

## Langues

- Français et anglais, avec un sélecteur FR / EN en haut à droite. Chaque lien de langue porte `lang` et `hreflang`, la langue courante `aria-current`.
- Anglais neutre, pour des tricoteuses du monde entier : ni britannismes (« maths », « tension », « ball band », « licence ») ni américanismes marqués. « Gauge » plutôt que « tension ».
- Mesures en cm, avec les pouces entre parenthèses en anglais : « 56 cm (22 in) ». Le formulaire anglais propose un choix cm / in pour le tour de tête et les hauteurs ; le français reste en cm.
- Aiguilles en mm, avec les tailles US et UK en anglais : « 4 mm (US 6 · UK 8) ».
- Vocabulaire tricot usuel : « bonnet en côtes 2/2, taille adulte », « 2x2 rib hat, adult size ». Un échantillon s’affiche toujours avec ses aiguilles.

## Ambiance : atelier chaleureux

Le logo actuel (maille en V et coche) reste. Fond crème, texte marine, terracotta en accent, motif discret de mailles en V derrière le haut de page.

| Rôle | Couleur | Contraste |
|---|---|---|
| Fond | `#F6F1E7` crème | — |
| Surface (cartes) | `#FFFCF6` | — |
| Texte | `#26244A` marine | 13:1 sur le fond |
| Texte secondaire | `#4A4662`, `#5A5670` | 8:1 et 6,2:1 |
| Accent texte et bouton principal | `#A8462A` terracotta foncée | 5,2:1 ; texte `#FFFCF6` dessus 5,7:1 |
| Terracotta du logo | `#E0714F` | 2,8:1 : décor seulement, jamais du texte |
| Bande sombre | `#26244A`, cartes `#33305E` | texte `#DCD6EA` 8,6:1 sur les cartes ; bouton `#F0A68C` avec texte marine 7,4:1 |

Typographies (Google Fonts) :

| Usage | Police |
|---|---|
| Titres | Fraunces 600 |
| Texte | Atkinson Hyperlegible, conçue pour la lisibilité |
| Chiffres (mailles, mesures) | JetBrains Mono |

## Pastilles d’origine d’un chiffre

Chaque valeur affichée porte une pastille : couleur, icône et nom écrit, jamais la couleur seule.

| Pastille FR | EN | Couleurs (texte / fond, contraste) | Sortes de source (`SourceKind`) |
|---|---|---|---|
| Échantillon | Swatch | `#2F5229` / `#DCE8D5`, 7:1 | `user_swatch` |
| Étiquette de la laine | Yarn label | `#6B4A0E` / `#F6E1B8`, 6,3:1 | `yarn_label` |
| Référence | Reference | `#24406E` / `#D8E1F0`, 7,8:1 | `fiber_library`, `reference_measurement` |
| Votre mesure | Your measurement | `#5E2F5E` / `#EADBEA`, 7,7:1 | `user_measurement` |
| Votre choix | Your choice | `#1F4F4B` / `#D3EAE6`, 7,3:1 | `user_input`, `person_decision` |

Un résultat du moteur (`engine`) ne porte pas de pastille mais une coche : « Calcul vérifié ». À confirmer : la pastille de `ravelry` et celle de `model_inference`, une hypothèse qui doit se distinguer d’une valeur mesurée.

Une source publiée se cite par sa référence exacte (« DROPS Children 49-25 »), en fin de phrase, sans logo ni mention de partenariat : on ne reprend qu’un chiffre. Avant une offre payante, les conditions des éditeurs cités sont à relire ([CLA-86](https://linear.app/claude-personnal/issue/CLA-86)).

Un doute s’affiche en encadré ambre, avec la raison et le geste attendu : « Lavez et bloquez votre échantillon avant de vous fier au calcul. Sinon, tricotez à vos risques et périls ! 😉 »

## Accessibilité

RGAA 4.1 AA : contrastes ci-dessus, cibles d’au moins 44 px, focus visible marine, clair (`#F0A68C`) sur la bande sombre, vrais liens et boutons, icônes décoratives masquées, mise en page qui passe en une colonne sur téléphone.

## Page d’accueil

1. En-tête : logo, « Calculer un bonnet », « Vérifier un patron », « Comment ça marche », sélecteur de langue.
2. Accroche « Tricotez à votre taille, du premier coup. » et une fiche d’exemple avec ses pastilles.
3. Comment ça marche : vous mesurez, knitproof calcule, vous gardez la main.
4. Légende des pastilles.
5. Par où commencer : « Je veux tricoter un bonnet », « J’ai déjà un patron ». Ces boutons ouvrent directement l’écran de calcul ou de vérification.
6. Réassurance : votre tension (EN : your gauge), aucun chiffre au hasard, une question plutôt qu’une supposition.
7. Pied de page : licence du code, lien « Pour les développeurs », accessibilité.

Les chiffres de la fiche d’exemple sont illustratifs : à remplacer par une sortie de `knitproof calc` avant la démo.

## Écrans de calcul et de vérification

- Chaque écran reprend l’en-tête de l’accueil : logo vers l’accueil, menu avec la page courante marquée (`aria-current`), sélecteur de langue. Pas de lien « Retour à l’accueil », qui doublerait le logo.
- Le titre et l’introduction couvrent toute la largeur ; le formulaire et les conseils commencent sur la même ligne.
- Résultat du calcul : sans les rangs de la tricoteuse, l’encadré « Hauteur : mesurez plutôt que compter » donne le bord et le corps en cm (« Corps : jusqu’à 19,3 cm »), les rangs en estimation, et un champ « Mes rangs pour 10 cm » pour recalculer sur place. Ces hauteurs viennent du moteur ([CLA-208](https://linear.app/claude-personnal/issue/CLA-208)). La calotte reste en rangs : elle suit les diminutions.
- Un écart de vérification dit « Juste » ou « Écart » en toutes lettres, avec le compte annoncé, le compte calculé, l’endroit et le pourquoi.
- Vérification : coller le texte, ou importer un patron en PDF ou en photo (marqué « Bientôt » tant que la lecture n’existe pas). Le texte lu est montré à la personne pour correction avant la vérification.

## Mode tricot

Sur téléphone et tablette, le résultat du calcul accompagne le tricot ([CLA-211](https://linear.app/claude-personnal/issue/CLA-211), après M3) : étapes à cocher, compteur de rangs −/+ à gros boutons sur l’étape en cours, option « Garder l’écran allumé ». La progression reste sur l’appareil ; les bornes du compteur viennent du moteur.
