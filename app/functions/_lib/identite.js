// Qui est connecté ? — pour une appli Cloudflare Pages derrière la porte commune (Cloudflare Access).
// À copier tel quel dans functions/_lib/identite.js de l'appli. Aucune dépendance.
//
//   import { identiteAccess } from './_lib/identite.js';
//   const qui = await identiteAccess(request, { aud: ['…'] });   // { email, name } ou null
//
// Deux façons de savoir, dans l'ordre :
//  1. le jeton signé que Access ajoute à chaque requête (en-tête Cf-Access-Jwt-Assertion, ou cookie
//     CF_Authorization) : on vérifie sa signature avec les clés publiques de l'équipe
//     (https://<équipe>.cloudflareaccess.com/cdn-cgi/access/certs, gardées 1 h en mémoire), son
//     émetteur, sa date, et — si on les connaît — les AUD attendus (l'identifiant de l'application
//     Access de CETTE appli, affiché par le robot « Porte commune ») ;
//  2. en secours, /cdn-cgi/access/get-identity sur sa propre adresse, avec le cookie reçu : Access
//     lui-même répond avec l'identité pour cette application.
// Le résultat est gardé 10 minutes par jeton, pour ne pas revérifier à chaque photo ou sonde.

const EQUIPE = 'falling-field-2b44.cloudflareaccess.com'; // l'équipe Zero Trust de la famille
const CACHE = new Map(); // empreinte du jeton → { jusqua, identite }
const DUREE = 10 * 60 * 1000;
let CLES = { jusqua: 0, parId: new Map() };

function cookie(request, nom) {
  const m = (request.headers.get('cookie') || '').match(new RegExp(`(?:^|;\\s*)${nom}=([^;]+)`));
  return m ? m[1] : null;
}
function b64url(s) {
  s = String(s).replace(/-/g, '+').replace(/_/g, '/');
  while (s.length % 4) s += '=';
  return Uint8Array.from(atob(s), (c) => c.charCodeAt(0));
}
async function empreinte(texte) {
  const h = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(texte));
  return Array.from(new Uint8Array(h), (b) => b.toString(16).padStart(2, '0')).join('');
}

async function clesDeLequipe(equipe) {
  if (CLES.jusqua > Date.now() && CLES.parId.size) return CLES.parId;
  const r = await fetch(`https://${equipe}/cdn-cgi/access/certs`);
  if (!r.ok) throw new Error(`certs ${r.status}`);
  const { keys = [] } = await r.json();
  const parId = new Map();
  for (const k of keys) {
    if (k.kty !== 'RSA' || (k.alg && k.alg !== 'RS256')) continue;
    parId.set(k.kid, await crypto.subtle.importKey('jwk', k, { name: 'RSASSA-PKCS1-v1_5', hash: 'SHA-256' }, false, ['verify']));
  }
  CLES = { jusqua: Date.now() + 60 * 60 * 1000, parId };
  return parId;
}

/** Vérifie le jeton Access : signature, émetteur, date, AUD (si fournis). → { email, name } ou null */
async function verifierJeton(jeton, { equipe, aud }) {
  const parts = jeton.split('.');
  if (parts.length !== 3) return null;
  const entete = JSON.parse(new TextDecoder().decode(b64url(parts[0])));
  const corps = JSON.parse(new TextDecoder().decode(b64url(parts[1])));
  if (entete.alg !== 'RS256' || !entete.kid) return null;
  const cle = (await clesDeLequipe(equipe)).get(entete.kid);
  if (!cle) return null;
  const ok = await crypto.subtle.verify('RSASSA-PKCS1-v1_5', cle, b64url(parts[2]), new TextEncoder().encode(`${parts[0]}.${parts[1]}`));
  if (!ok) return null;
  const maintenant = Math.floor(Date.now() / 1000);
  if (corps.iss !== `https://${equipe}`) return null;
  if (typeof corps.exp !== 'number' || corps.exp < maintenant - 60) return null;
  if (typeof corps.nbf === 'number' && corps.nbf > maintenant + 60) return null;
  if (aud && aud.length) {
    const auds = Array.isArray(corps.aud) ? corps.aud : [corps.aud];
    if (!auds.some((a) => aud.includes(a))) return null;
  }
  if (typeof corps.email !== 'string' || !corps.email.includes('@')) return null;
  return { email: corps.email.toLowerCase(), name: typeof corps.name === 'string' ? corps.name : '' };
}

/** En secours : Access lui-même, pour cette adresse. */
async function demanderAAccess(request, jeton) {
  const url = new URL(request.url);
  url.pathname = '/cdn-cgi/access/get-identity';
  url.search = '';
  const r = await fetch(url.toString(), {
    headers: { cookie: `CF_Authorization=${jeton}`, 'Cf-Access-Jwt-Assertion': jeton },
    redirect: 'manual',
  });
  if (!r.ok) return null;
  const d = await r.json();
  if (!d || typeof d.email !== 'string' || !d.email.includes('@')) return null;
  return { email: d.email.toLowerCase(), name: typeof d.name === 'string' ? d.name : '' };
}

/**
 * L'identité Access de la requête, ou null si la personne n'est pas passée par la porte.
 * options.aud : les AUD acceptés (recommandé) · options.equipe : l'équipe Zero Trust.
 */
export async function identiteAccess(request, options = {}) {
  const jeton = request.headers.get('Cf-Access-Jwt-Assertion') || cookie(request, 'CF_Authorization');
  if (!jeton) return null;
  const cle = await empreinte(jeton);
  const maintenant = Date.now();
  const connu = CACHE.get(cle);
  if (connu && connu.jusqua > maintenant) return connu.identite;

  const equipe = options.equipe || EQUIPE;
  let identite = null;
  try {
    identite = await verifierJeton(jeton, { equipe, aud: options.aud });
  } catch {
    identite = null;
  }
  if (!identite) {
    try {
      identite = await demanderAAccess(request, jeton);
    } catch {
      identite = null;
    }
  }
  if (CACHE.size > 500) CACHE.clear();
  CACHE.set(cle, { jusqua: maintenant + (identite ? DUREE : 30 * 1000), identite });
  return identite;
}
