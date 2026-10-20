// Extrait le contenu écrit dans platoz.html (cartes, sous-titres, niveaux, règles) vers contenu-defaut.json,
// pour que la page admin parte de ce que le jeu contient vraiment.
const fs = require("fs"), vm = require("vm");
const src = fs.readFileSync(__dirname + "/../platoz.html", "utf8");
const block = (start, end) => { const a = src.indexOf(start); if (a < 0) throw new Error(start); return src.slice(a, src.indexOf(end, a) + end.length); };
const code = [block("const C = {", "\n};"), block("const TYPES = {", "\n};"), block("const LEVELS = [", "\n];"), block("const TUTO = {", "\n};"), block("const DEUX = [", "\n];"), block("const PROPOSE = {", "\n};")].join("\n")
  + "\n({ C, TYPES, LEVELS, TUTO, DEUX, PROPOSE })";
const o = vm.runInNewContext(code, {});
const out = {
  cartes: o.C, deux: o.DEUX,
  noms: Object.fromEntries(Object.entries(o.TYPES).map(([k, t]) => [k, t.label])),
  desc: Object.fromEntries(Object.entries(o.TYPES).map(([k, t]) => [k, t.desc])),
  levels: o.LEVELS.map(l => l.desc), levelNames: o.LEVELS.map(l => l.name), tuto: o.TUTO, champs: o.PROPOSE
};
fs.writeFileSync(__dirname + "/../contenu-defaut.json", JSON.stringify(out));
console.log("contenu-defaut.json :", Object.entries(out.cartes).map(([k, v]) => k + " " + v.length).join(", "));
