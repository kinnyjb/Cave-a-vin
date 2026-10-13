/**
 * La porte de TOUTE l'appli Cave — la porte commune de la famille (Cloudflare Access,
 * connexion Google), mise en place le 13/10/2026 à la demande de Jean-Benoît.
 *
 * Jusque-là l'appli était ouverte à qui avait l'adresse : lire, ajouter, modifier,
 * supprimer, et lancer le robot GitHub sans limite. Désormais, Cloudflare Pages exécute
 * ce fichier avant CHAQUE requête (page, photos, /api/robot) : sans une personne reconnue
 * par Access, rien ne sort du serveur.
 *
 * La liste des personnes et la connexion Google sont réglées depuis kinnyjb/factures-app,
 * dossier porte-commune/ (« Porte · Cave à vin »). Ici on vérifie le jeton qu'Access
 * ajoute à chaque requête (_lib/identite.js : signature de l'équipe, AUD de l'appli).
 * Pas de code de secours : l'appli n'en a jamais eu, et le robot n'appelle pas l'adresse.
 */
import { identiteAccess } from "./_lib/identite.js";

/* l'identifiant (AUD) de l'application Access « Porte · Cave à vin », donné par le robot */
const ACCESS_AUD = ["a4e99b0aa4180476af47c3e33ba609ea9e64deb856ffed05524b74c8b503c072"];

export async function onRequest({ request, data, next }) {
  const qui = await identiteAccess(request, { aud: ACCESS_AUD });
  if (!qui) {
    const url = new URL(request.url);
    if (url.pathname.startsWith("/api/"))
      return new Response(JSON.stringify({ erreur: "Connecte-toi avec ton compte Google pour entrer dans la cave.", code: "connexion" }),
        { status: 401, headers: { "Content-Type": "application/json", "Cache-Control": "no-store" } });
    /* la porte commune est devant : on n'arrive ici que si le jeton manque ou ne se vérifie pas.
       On renvoie vers la sortie Access, qui ramène à l'écran Google. */
    return new Response("Connecte-toi avec ton compte Google pour entrer dans la cave.", {
      status: 401,
      headers: { "Content-Type": "text/plain; charset=utf-8", "Cache-Control": "no-store", Refresh: "0; url=/cdn-cgi/access/logout" },
    });
  }
  data.qui = qui;
  return next();
}
