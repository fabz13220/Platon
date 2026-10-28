#!/usr/bin/env bash
# Construit index.html (site GitHub) à partir de platoz.html (même fichier que l'artifact Claude),
# en ajoutant l'en-tête qui fait marcher l'affichage téléphone et l'installation comme une appli.
set -euo pipefail
cd "$(dirname "$0")"
{
cat <<'H'
<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no, viewport-fit=cover">
<meta name="theme-color" content="#061224">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="BLIZ">
<!-- pas de barre d'état « black-translucent » : avec iOS 26 elle raccourcit la page et laisse une bande noire en bas (bug WebKit 301108) ; la barre de l'heure prend theme-color -->
<!-- comme dans le lecteur Claude : le contenu commence sous l'heure et la batterie -->
<style>:root{padding-top:env(safe-area-inset-top,0px)}</style>
<meta name="build" content="@BUILD@">
<link rel="manifest" href="manifest.webmanifest">
<link rel="apple-touch-icon" href="icon-180.png?v=6">
<link rel="icon" type="image/png" href="icon-192.png?v=6">
<link rel="apple-touch-startup-image" href="splash/splash-1170x2532.png?v=5" media="(device-width: 390px) and (device-height: 844px) and (-webkit-device-pixel-ratio: 3) and (orientation: portrait)">
<link rel="apple-touch-startup-image" href="splash/splash-1179x2556.png?v=5" media="(device-width: 393px) and (device-height: 852px) and (-webkit-device-pixel-ratio: 3) and (orientation: portrait)">
<link rel="apple-touch-startup-image" href="splash/splash-1284x2778.png?v=5" media="(device-width: 428px) and (device-height: 926px) and (-webkit-device-pixel-ratio: 3) and (orientation: portrait)">
<link rel="apple-touch-startup-image" href="splash/splash-1290x2796.png?v=5" media="(device-width: 430px) and (device-height: 932px) and (-webkit-device-pixel-ratio: 3) and (orientation: portrait)">
<link rel="apple-touch-startup-image" href="splash/splash-750x1334.png?v=5" media="(device-width: 375px) and (device-height: 667px) and (-webkit-device-pixel-ratio: 2) and (orientation: portrait)">
<link rel="apple-touch-startup-image" href="splash/splash-828x1792.png?v=5" media="(device-width: 414px) and (device-height: 896px) and (-webkit-device-pixel-ratio: 2) and (orientation: portrait)">
<link rel="apple-touch-startup-image" href="splash/splash-1125x2436.png?v=5" media="(device-width: 375px) and (device-height: 812px) and (-webkit-device-pixel-ratio: 3) and (orientation: portrait)">
<link rel="apple-touch-startup-image" href="splash/splash-1242x2688.png?v=5" media="(device-width: 414px) and (device-height: 896px) and (-webkit-device-pixel-ratio: 3) and (orientation: portrait)">
<link rel="apple-touch-startup-image" href="splash/splash-1206x2622.png?v=5" media="(device-width: 402px) and (device-height: 874px) and (-webkit-device-pixel-ratio: 3) and (orientation: portrait)">
<link rel="apple-touch-startup-image" href="splash/splash-1320x2868.png?v=5" media="(device-width: 440px) and (device-height: 956px) and (-webkit-device-pixel-ratio: 3) and (orientation: portrait)">
<link rel="apple-touch-startup-image" href="splash/splash-1242x2208.png?v=5" media="(device-width: 414px) and (device-height: 736px) and (-webkit-device-pixel-ratio: 3) and (orientation: portrait)">
<link rel="apple-touch-startup-image" href="splash/splash-1080x2340.png?v=5" media="(device-width: 360px) and (device-height: 780px) and (-webkit-device-pixel-ratio: 3) and (orientation: portrait)">
H
cat platoz.html
cat <<'U'
<script>
// GitHub Pages fait garder l'ancienne page jusqu'à 10 min dans le téléphone : à l'ouverture (et au retour dans l'appli),
// on va chercher la dernière version sans passer par cette mémoire, et on recharge si elle a changé.
// Jamais en pleine partie, ni quand des joueurs sont déjà ajoutés (ils seraient perdus).
(function () {
  if (!/github\.io$/.test(location.hostname) || !window.fetch) return;
  var mine = document.querySelector('meta[name="build"]').content, busy = false;
  var calme = function () {
    try { return !S.inGame && !ON.ctx && !S.names.length; } catch (e) { return false; }
  };
  var check = function () {
    if (busy || document.hidden || !calme()) return;
    busy = true;
    fetch(location.href, { cache: "reload" }).then(function (r) { return r.ok ? r.text() : ""; }).then(function (t) {
      var m = t.match(/<meta name="build" content="([^"]+)"/), k = "maj-" + (m && m[1]);
      if (!m || m[1] === mine || !calme()) return;
      try { if (sessionStorage.getItem(k)) return; sessionStorage.setItem(k, "1"); } catch (e) {}
      location.reload();
    }).catch(function () {}).then(function () { busy = false; });
  };
  setTimeout(check, 300);
  document.addEventListener("visibilitychange", check);
})();
// sans internet : sw.js garde la page et les polices dans le téléphone
(function () {
  var on = /github\.io$/.test(location.hostname);
  try { on = on || localStorage.getItem("scandale:sw") === "1"; } catch (e) {}
  if (on && "serviceWorker" in navigator) addEventListener("load", function () { 
    navigator.serviceWorker.register("sw.js").then(function () { return navigator.serviceWorker.ready; }).then(function (reg) {
      var urls = performance.getEntriesByType("resource").map(function (r) { return r.name; }).filter(function (u) { return /fonts\.(googleapis|gstatic)\.com/.test(u); });
      if (reg.active) reg.active.postMessage({ keep: urls });
    }).catch(function () {});
  });
})();
</script>
U
} > index.html
# empreinte de la version : l'appli la compare avec celle en ligne pour se mettre à jour
sed -i "s/@BUILD@/$(sha1sum platoz.html | cut -c1-12)/" index.html
# contenu de départ de la page admin (cartes, textes) tiré de platoz.html
node outils/defaut.js
