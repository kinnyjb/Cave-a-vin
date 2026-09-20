/**
 * Déclenche le robot Cave (GitHub Actions) depuis l'appli.
 * Cloudflare Pages — route : POST /api/robot
 *
 *   { "action": "bouteille", "bouteille": {...} }
 *
 * Variables à définir dans le projet Cloudflare Pages :
 *   GH_TOKEN  jeton GitHub fine-grained, permission "Actions: read and write"
 *   GH_REPO   "kinnyjb/Cave-a-vin"
 */
export async function onRequestPost({ request, env }) {
  const json = (o, s = 200) =>
    new Response(JSON.stringify(o), { status: s, headers: { "Content-Type": "application/json" } });

  if (!env.GH_TOKEN || !env.GH_REPO)
    return json({ erreur: "Robot non configuré (GH_TOKEN / GH_REPO manquants)" }, 500);

  let corps;
  try {
    corps = await request.json();
  } catch {
    return json({ erreur: "JSON invalide" }, 400);
  }

  if (corps.action !== "bouteille") return json({ erreur: "action inconnue" }, 400);
  if (!corps.bouteille) return json({ erreur: "bouteille requise" }, 400);
  const texte = typeof corps.bouteille === "string" ? corps.bouteille : JSON.stringify(corps.bouteille);
  // garde-fou : une bouteille pèse moins d'1 Ko, au-delà c'est une erreur d'appel
  if (texte.length > 20000) return json({ erreur: "bouteille trop volumineuse" }, 413);
  const inputs = { action: "bouteille", bouteille: texte };

  const r = await fetch(
    `https://api.github.com/repos/${env.GH_REPO}/actions/workflows/robot.yml/dispatches`,
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${env.GH_TOKEN}`,
        Accept: "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "Content-Type": "application/json",
        "User-Agent": "cave-appli",
      },
      body: JSON.stringify({ ref: "main", inputs }),
    }
  );

  if (r.status === 204)
    return json({
      ok: true,
      message: "Enregistré dans la cave commune. Ça apparaîtra dans l'appli d'ici 2 à 3 minutes.",
    });

  const detail = await r.text();
  return json({ erreur: `GitHub a répondu ${r.status}`, detail: detail.slice(0, 300) }, 502);
}
