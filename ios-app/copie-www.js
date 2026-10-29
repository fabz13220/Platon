// Copie le site (index.html généré par build.sh + icônes + contenu) dans www/, ce que l'appli iPhone emporte.
// Tout est dans l'appli : elle s'ouvre même sans internet.
const fs = require("fs"), path = require("path");
const src = path.join(__dirname, ".."), www = path.join(__dirname, "www");
fs.rmSync(www, { recursive: true, force: true });
fs.mkdirSync(www);
for (const f of ["index.html", "contenu-defaut.json", "manifest.webmanifest", "icon-180.png", "icon-192.png", "icon-512.png"])
  fs.copyFileSync(path.join(src, f), path.join(www, f));
console.log("www prêt");
