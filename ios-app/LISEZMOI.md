# BLIZ pour iPhone (Capacitor)

Sur un Mac avec Xcode et Node installés, dans ce dossier :

    npm install
    npm run ios            # copie le site, met à jour, ouvre Xcode

Dans Xcode : choisir ton équipe (Signing & Capabilities), brancher l'iPhone, appuyer sur ▶.

Avant chaque nouvelle version : lancer `./build.sh` à la racine, puis `npm run ios`.
