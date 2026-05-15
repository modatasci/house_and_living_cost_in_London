// Cloudflare Pages Function: /votes
//   GET  → { counts: Record<feature_key, number> }
//   POST → { ok: true } ; body { session_id, feature_key } ; one permanent vote
import { FEATURE_KEYS } from "./_features";

interface Env {
  DB: D1Database;
}

const json = (data: unknown, status = 200) =>
  new Response(JSON.stringify(data), {
    status,
    headers: { "content-type": "application/json" },
  });

export const onRequestGet: PagesFunction<Env> = async ({ env }) => {
  const { results } = await env.DB.prepare(
    "SELECT feature_key, COUNT(*) AS c FROM feature_votes GROUP BY feature_key"
  ).all<{ feature_key: string; c: number }>();

  const counts: Record<string, number> = {};
  for (const key of FEATURE_KEYS) counts[key] = 0;
  for (const row of results ?? []) counts[row.feature_key] = row.c;

  return json({ counts });
};

export const onRequestPost: PagesFunction<Env> = async ({ request, env }) => {
  let body: { session_id?: unknown; feature_key?: unknown };
  try {
    body = await request.json();
  } catch {
    return json({ error: "invalid JSON" }, 400);
  }

  const sessionId = typeof body.session_id === "string" ? body.session_id.trim() : "";
  const featureKey = typeof body.feature_key === "string" ? body.feature_key.trim() : "";

  if (!sessionId || sessionId.length > 100) {
    return json({ error: "invalid session_id" }, 400);
  }
  if (!FEATURE_KEYS.has(featureKey)) {
    return json({ error: "unknown feature_key" }, 400);
  }

  await env.DB.prepare(
    "INSERT OR IGNORE INTO feature_votes (session_id, feature_key) VALUES (?, ?)"
  )
    .bind(sessionId, featureKey)
    .run();

  return json({ ok: true });
};
