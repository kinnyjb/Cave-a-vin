# CLAUDE.md — la cave à vin de la maison

> 📌 **Ce dépôt tient debout tout seul.** Pour travailler sur la cave ou sur
> l'appli, il n'y a rien à savoir des autres projets de la maison. Tout ce qui
> suit suffit.
>
> Calqué sur `kinnyjb/recettes` (même modèle : Cloudflare Pages + robot GitHub
> Actions), mais **dépôt indépendant** — sa propre adresse, son propre projet
> Cloudflare, sa propre base de données si un jour il en faut une. Rien n'est
> partagé avec `kinnyjb/recettes` pour l'instant : aucun lien de navigation,
> aucune donnée commune. Si un lien devient utile un jour (suggérer un vin
> depuis une recette, par exemple), il se décidera à ce moment-là — pas avant.

---

# 🚀 Les commandes

| Commande | Ce qu'elle fait |
|---|---|
| `./lancer bouteille '<json>'` | ajoute une bouteille à la cave |
| `./lancer bouteille --modifier <id> --fichier <f>` | réécrit une bouteille **en place** |
| `./lancer bouteille --supprimer <id>` | la retire |
| `./lancer bouteille --ouvrir <id> [--n 2]` | décrémente le stock (bouteille bue) |
| `./lancer accord '<plat>'` | suggère une bouteille de la cave pour ce plat |
| `./lancer appli` | reconstruit l'appli |

*(Sur Windows, `lancer` sans le `./`. Aucun environnement à installer : tout tourne
avec le Python déjà présent sur le système.)*

# 📁 Où vit quoi

```
bouteilles/                  ← LA CAVE. Un fichier JSON par référence (par lot).
  photos/                    ← les photos d'étiquette, recopiées vers l'appli au build
cave.py                      ← le point d'entrée, appelé par lancer / lancer.bat
tools/
  ajouter_bouteille.py        ← écrit, modifie, supprime, ouvre une bouteille
  accord.py                    ← le moteur d'accords mets-vin
  accords.json                 ← la table de référence (plats, cépages)
  build_appli.py               ← construit l'appli
  faire_icone.py               ← fabrique les icônes de l'appli
app-src/cave.src.html         ← LA SOURCE de l'appli
app/                          ← ce qui est mis en ligne (généré, ne pas éditer)
app/functions/api/robot.js    ← la passerelle vers GitHub Actions
```

🔴 **Ne jamais éditer `app/index.html` à la main** — il est régénéré à chaque
build depuis `app-src/cave.src.html`. Toute modification y est perdue.

# ⚠️ Les règles qui ne se discutent pas

1. **La cave ne contient que ce qu'il y a physiquement dans la maison.** Ce
   n'est ni un carnet de dégustation de bouteilles bues il y a longtemps, ni
   une liste d'envies — juste le stock réel. Une bouteille bue s'`--ouvrir`
   (le stock baisse) ; une bouteille qui n'est plus là du tout se `--supprimer`.
2. **Ne jamais modifier ni supprimer la bouteille de quelqu'un d'autre** sans
   son accord. Plusieurs personnes de la maison écrivent depuis leur téléphone.
3. **Ne jamais inventer une note de dégustation ou une info qu'on ne connaît
   pas.** Le champ `note` est ce que la maison en pense elle-même — pas une
   fiche promotionnelle générée. Ce qui manque (millésime illisible sur
   l'étiquette, cépage inconnu) se demande, ne s'invente pas.
4. **Les suggestions d'accord sont des repères, jamais une prescription.**
   `tools/accords.json` encode des conventions œnologiques classiques et
   générales — ce n'est ni un avis sur la qualité d'une bouteille, ni une
   vérité qui prime sur l'envie du moment.

# 🗣️ Ton

Chaleureux, direct, sans blabla. Phrases courtes. L'appli est ouverte à toute
la maison, pas seulement à qui l'a créée.

---

# 🍷 Les trois écrans

1. **Cave** — l'écran d'accueil : la liste des bouteilles, recherche sur le
   nom, le producteur, la région et les cépages, filtre par couleur. Chaque
   bouteille affiche ce qu'il en reste ; à zéro, elle dit « plus en cave » au
   lieu de disparaître — c'est aussi une mémoire de ce qu'on a aimé.
2. **Accord** — on tape ou on pioche ce qu'on mange, l'appli propose les
   bouteilles de la cave qui conviennent le mieux, classées par couleur puis
   par corps. Toujours à partir de ce qu'il y a vraiment en cave.
3. **Ajouter** — le formulaire. Le brouillon est gardé en local. C'est aussi
   l'écran de **modification** (voir ci-dessous) et d'**ouverture** (bouton
   « Ouvrir une bouteille » sur le détail d'une référence).

## ✏️ Modifier, supprimer, ouvrir une bouteille (depuis le téléphone)
Le détail d'une bouteille porte un bouton **Modifier**, qui rouvre l'onglet
Ajouter, pré-rempli, avec un bandeau « Tu modifies X » et, tout en bas, un
bloc **Supprimer** en deux appuis (le premier avertit, le second envoie).

- 🔑 **La bouteille garde son fichier et son identifiant**, même si son nom
  change. C'est ce qui fait qu'elle garde son historique (nombre de fois
  servie, dernier service) en corrigeant une faute de frappe.
- 🔑 **Le brouillon local est mis de côté puis remis**, comme dans l'appli
  Recettes : on ne perd pas une bouteille en cours de saisie en corrigeant
  autre chose ailleurs.
- La signature d'origine (`par`) **ne change pas** : on ajoute `modifie_par`
  et `modifie_le`.
- **Ouvrir une bouteille** décrémente `quantite` de 1 (ou plus, `--n`),
  incrémente `fois_servie` et note `dernier_service`. Ça passe par le même
  robot (2 à 3 minutes), pas par une base de données instantanée : ouvrir une
  bouteille n'a pas besoin d'être vu à la seconde près sur l'autre téléphone.

**L'opération voyage dans le JSON**, pas dans le workflow :

```json
{"_op": "modifier",  "id": "2026-09-20-chateau-truc", "nom": "…", ...}
{"_op": "supprimer", "id": "2026-09-20-chateau-truc", "par": "Camille"}
{"_op": "ouvrir",    "id": "2026-09-20-chateau-truc", "n": 1}
```

> 🔴 L'identifiant est comparé **aux fichiers réellement présents** dans
> `bouteilles/`, jamais reconstruit à partir du texte reçu.

## 🍽 Le moteur d'accords
`tools/accord.py` (et son miroir en JavaScript dans `cave.src.html`) associe un
plat, en texte libre, à une couleur et un corps de vin attendus, via
`tools/accords.json`. Le plat est retrouvé par le même algorithme que le
moteur nutrition de Recettes (égalité, puis inclusion, puis mots en commun) —
« un gros gigot d'agneau de 7 heures » retombe sur « gigot d'agneau ».

Un ingrédient/plat inconnu de `tools/accords.json` n'est pas une erreur :
**compléter la table** plutôt que deviner à la volée dans le code.

## 📸 Reprendre une bouteille depuis une photo d'étiquette
Même principe que les recettes de famille dans `kinnyjb/recettes` :

1. **Lire l'étiquette et retranscrire fidèlement** — nom, producteur, millésime,
   région, cépages tels qu'écrits.
2. **Demander ce qui manque**, plutôt que l'inventer : quantité en cave,
   corps du vin si les cépages ne le disent pas.
3. Écrire avec `./lancer bouteille '<json>'`, en mettant `"par"` = la personne
   qui ajoute la bouteille.
4. La photo va dans `bouteilles/photos/`, et son nom de fichier dans le champ
   `photo` de la bouteille.

# 🔌 Comment ça tient debout

Le chemin d'une bouteille ajoutée depuis le téléphone :

```
appli → POST /api/robot {action:"bouteille"} → GitHub Actions
   → tools/ajouter_bouteille.py → bouteilles/*.json → commit → mise en ligne
```

Compter **2 à 3 minutes**. Pas de base D1 pour l'instant : à la différence de
la liste de courses de Recettes, une cave de ~50 bouteilles n'a pas besoin
d'une seconde de latence — le rythme du commit GitHub suffit très largement.
Si un jour il faut un compteur partagé plus réactif, le modèle `courses.js` /
`semaine.js` de `kinnyjb/recettes` est là pour s'en inspirer.

## 🛠 Mise en place encore à faire (côté humain)

Ce dépôt a été préparé par Claude Code, mais trois choses ne peuvent se faire
que depuis un compte Cloudflare / GitHub, pas depuis cette session :

1. **Projet Cloudflare Pages** — nommé `cave-appli` dans `.github/workflows/robot.yml`.
   Il se crée tout seul au premier passage du robot (`wrangler pages project create`),
   mais le dépôt doit d'abord avoir les secrets suivants (`Settings → Secrets and
   variables → Actions` sur GitHub) :
   - `CLOUDFLARE_API_TOKEN` — un jeton avec la permission "Cloudflare Pages: Edit".
   - `CLOUDFLARE_ACCOUNT_ID` — l'identifiant du compte Cloudflare.
2. **Variables du projet Pages** (`Settings → Environment variables` sur le
   projet `cave-appli`, une fois créé) :
   - `GH_TOKEN` — un jeton GitHub fine-grained, permission "Actions: read and write",
     limité à ce dépôt.
   - `GH_REPO` — `kinnyjb/Cave-a-vin`.
   Sans ces deux variables, `/api/robot` répond une erreur claire à l'écran —
   rien ne casse, mais rien ne s'enregistre non plus.
3. **Les bouteilles elles-mêmes.** `bouteilles/` est vide au départ : la cave
   se remplit une bouteille à la fois, à la main ou en photographiant les
   étiquettes.

# 🔒 Ce qui n'est PAS protégé

**L'appli est ouverte à qui a l'adresse.** Pas de compte, pas de mot de passe :
n'importe qui peut lire, ajouter, modifier et supprimer une bouteille. Seule
l'obscurité de l'URL protège la cave — même situation que `kinnyjb/recettes`,
et la même question reste ouverte : un code de la maison, une lecture libre
et une écriture protégée, ou rien.

# 🧪 Comment vérifier avant de publier

La vérification se fait **dans un navigateur, sur le fichier construit**.

```
python3 tools/build_appli.py
node --input-type=module -e "…"        # le JS de la page est-il valide ?
node <script playwright>                # ouvrir file://…/app/index.html
```

`/api/robot` ne peut pas être testé en local (il appelle GitHub) : on vérifie
le formulaire et l'affichage jusqu'à l'appel réseau, qu'on peut intercepter
dans Playwright pour vérifier le corps envoyé.
