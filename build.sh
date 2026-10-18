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
<meta name="theme-color" content="#0B0720">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="Platoz">
<link rel="manifest" href="manifest.webmanifest">
<link rel="apple-touch-icon" href="icon-180.png">
<link rel="icon" type="image/png" href="icon-192.png">
H
cat platoz.html
} > index.html
