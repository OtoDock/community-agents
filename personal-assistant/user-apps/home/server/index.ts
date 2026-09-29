// Home — the Personal Assistant's personal page: the weather for one city
// and one to-do list, kept in this app's own database. The platform deploys
// one copy per member, so there is one owner: they write from the page, the
// assistant writes from a chat (basis "agent"), anyone else the platform
// lets in reads.

import { Database } from "bun:sqlite";

const PORT = Number(process.env.PORT || 3000);
const DATA_DIR = process.env.OTODOCK_DATA_DIR || "/app/data";
const WEATHER_TTL = 30 * 60 * 1000;
const MAX_TODOS = 200;
const FORECAST_DAYS = 6; // today + 5

const db = new Database(DATA_DIR + "/app.db", { create: true });
db.exec("PRAGMA journal_mode = WAL");

// Additive only: the previous release keeps serving this file during a deploy.
db.exec(`
  CREATE TABLE IF NOT EXISTS settings (
    key        TEXT PRIMARY KEY,
    json       TEXT NOT NULL,
    updated_at TEXT NOT NULL
  );
  CREATE TABLE IF NOT EXISTS todos (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    text       TEXT NOT NULL,
    done       INTEGER NOT NULL DEFAULT 0,
    position   INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    done_at    TEXT
  );
  CREATE TABLE IF NOT EXISTS cache (
    key        TEXT PRIMARY KEY,
    json       TEXT NOT NULL,
    fetched_at INTEGER NOT NULL
  );
`);

// ---------- who is calling ----------

type Viewer = { name: string; canEdit: boolean };

function claimOf(req: Request): any {
  const raw = req.headers.get("x-otodock-viewer") || "";
  try {
    const part = raw.split(".")[1] || raw;
    const pad = part.length % 4 === 0 ? "" : "=".repeat(4 - (part.length % 4));
    const s = part.replace(/-/g, "+").replace(/_/g, "/") + pad;
    return JSON.parse(new TextDecoder().decode(Uint8Array.from(atob(s), (c) => c.charCodeAt(0)))) || {};
  } catch {
    return {};
  }
}

function viewerOf(req: Request): Viewer {
  const basis = req.headers.get("x-otodock-basis") || "viewer";
  const claim = claimOf(req);
  const principal = String(claim.principal || (basis === "viewer" ? "viewer" : basis));
  if (principal === "agent" || basis === "agent") return { name: "your assistant", canEdit: true };
  if (principal !== "viewer" || claim.external) return { name: "a visitor", canEdit: false };
  const role = String(claim.role || "");
  return {
    name: String(claim.name || claim.username || ""),
    // The owner of a personal app is its manager; a colleague it was shared
    // with is a viewer of it and only looks.
    canEdit: role === "manager" || role === "admin",
  };
}

// ---------- settings ----------

type Settings = { city: string; lat: number | null; lon: number | null; tz: string; units: string };

const BLANK: Settings = { city: "", lat: null, lon: null, tz: "auto", units: "celsius" };

function readSettings(): Settings {
  const row = db.query("SELECT json FROM settings WHERE key = 'home'").get() as any;
  if (!row) return { ...BLANK };
  const raw = JSON.parse(row.json) || {};
  const out: any = { ...BLANK };
  for (const k of Object.keys(BLANK)) if (k in raw) out[k] = raw[k];
  return out as Settings;
}

function writeSettings(patch: any): Settings {
  const cur = readSettings();
  const num = (x: any, fallback: number | null) =>
    x === null ? null : typeof x === "number" && Number.isFinite(x) ? x : fallback;
  const next: Settings = {
    city: typeof patch.city === "string" ? patch.city.trim().slice(0, 120) : cur.city,
    lat: "lat" in patch ? num(patch.lat, cur.lat) : cur.lat,
    lon: "lon" in patch ? num(patch.lon, cur.lon) : cur.lon,
    tz: typeof patch.tz === "string" && patch.tz ? patch.tz.slice(0, 60) : cur.tz,
    units: "units" in patch ? (patch.units === "fahrenheit" ? "fahrenheit" : "celsius") : cur.units,
  };
  if (!next.city) { next.lat = null; next.lon = null; next.tz = "auto"; }
  db.query(
    "INSERT INTO settings (key, json, updated_at) VALUES ('home', ?, ?) " +
      "ON CONFLICT(key) DO UPDATE SET json = excluded.json, updated_at = excluded.updated_at"
  ).run(JSON.stringify(next), new Date().toISOString());
  return next;
}

// ---------- weather (cached) ----------

function cacheGet(key: string, ttl: number): any | null {
  const row = db.query("SELECT json, fetched_at FROM cache WHERE key = ?").get(key) as any;
  if (!row || Date.now() - row.fetched_at > ttl) return null;
  return JSON.parse(row.json);
}

function cacheStale(key: string): any | null {
  const row = db.query("SELECT json FROM cache WHERE key = ?").get(key) as any;
  return row ? { ...JSON.parse(row.json), stale: true } : null;
}

function cachePut(key: string, value: any) {
  db.query(
    "INSERT INTO cache (key, json, fetched_at) VALUES (?, ?, ?) " +
      "ON CONFLICT(key) DO UPDATE SET json = excluded.json, fetched_at = excluded.fetched_at"
  ).run(key, JSON.stringify(value), Date.now());
}

function weatherKey(s: Settings): string {
  return "weather:" + (s.lat as number).toFixed(3) + "," + (s.lon as number).toFixed(3) + "," + s.units;
}

async function fetchWeather(s: Settings) {
  const u = new URL("https://api.open-meteo.com/v1/forecast");
  u.searchParams.set("latitude", String(s.lat));
  u.searchParams.set("longitude", String(s.lon));
  u.searchParams.set("current", "temperature_2m,apparent_temperature,relative_humidity_2m,weather_code,wind_speed_10m,is_day");
  u.searchParams.set("daily", "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max,sunrise,sunset");
  u.searchParams.set("timezone", s.tz && s.tz !== "auto" ? s.tz : "auto");
  u.searchParams.set("forecast_days", String(FORECAST_DAYS));
  if (s.units === "fahrenheit") u.searchParams.set("temperature_unit", "fahrenheit");
  const r = await fetch(u.toString(), { signal: AbortSignal.timeout(15000) });
  if (!r.ok) throw new Error("open-meteo " + r.status);
  const j: any = await r.json();
  return { current: j.current || null, daily: j.daily || null, units: j.current_units || null,
           tz: j.timezone || s.tz, at: new Date().toISOString() };
}

async function weatherFor(s: Settings, force = false) {
  if (s.lat === null || s.lon === null) return null;
  const key = weatherKey(s);
  if (!force) {
    const hit = cacheGet(key, WEATHER_TTL);
    if (hit) return hit;
  }
  try {
    const fresh = await fetchWeather(s);
    cachePut(key, fresh);
    return fresh;
  } catch (e) {
    console.log("weather fetch failed: " + e);
    return cacheStale(key);
  }
}

async function geocode(q: string) {
  const u = new URL("https://geocoding-api.open-meteo.com/v1/search");
  u.searchParams.set("name", q);
  u.searchParams.set("count", "6");
  const r = await fetch(u.toString(), { signal: AbortSignal.timeout(12000) });
  if (!r.ok) throw new Error("geocoding " + r.status);
  const j: any = await r.json();
  return (j.results || []).map((g: any) => ({
    name: String(g.name || ""), admin1: String(g.admin1 || ""), country: String(g.country || ""),
    lat: g.latitude, lon: g.longitude, tz: g.timezone || "auto",
  }));
}

// ---------- to-dos ----------

const TODOS_SQL =
  "SELECT id, text, done, position, created_at, done_at FROM todos " +
  "ORDER BY done ASC, CASE WHEN done = 0 THEN position ELSE 0 END ASC, done_at DESC, id ASC";

function todos() {
  return db.query(TODOS_SQL).all();
}

function openIds(): number[] {
  return (db.query("SELECT id FROM todos WHERE done = 0 ORDER BY position ASC, id ASC").all() as any[]).map((r) => r.id);
}

function renumber(ids: number[]) {
  const upd = db.query("UPDATE todos SET position = ? WHERE id = ?");
  ids.forEach((id, i) => upd.run(i, id));
}

function addTodo(text: string) {
  const count = (db.query("SELECT COUNT(*) AS n FROM todos").get() as any).n;
  if (count >= MAX_TODOS) throw new Error("the list is full (" + MAX_TODOS + " items); clear some done ones");
  db.query("INSERT INTO todos (text, done, position, created_at) VALUES (?, 0, ?, ?)").run(
    text, openIds().length, new Date().toISOString());
}

function patchTodo(id: number, patch: any) {
  const row = db.query("SELECT id, done FROM todos WHERE id = ?").get(id) as any;
  if (!row) return false;
  if (typeof patch.text === "string") {
    const text = patch.text.trim().slice(0, 500);
    if (text) db.query("UPDATE todos SET text = ? WHERE id = ?").run(text, id);
  }
  if (typeof patch.done === "boolean" && patch.done !== !!row.done) {
    db.query("UPDATE todos SET done = ?, done_at = ? WHERE id = ?").run(
      patch.done ? 1 : 0, patch.done ? new Date().toISOString() : null, id);
    const ids = openIds().filter((x) => x !== id);
    if (!patch.done) ids.push(id);
    renumber(ids);
  }
  if (typeof patch.position === "number" && Number.isFinite(patch.position)) {
    const ids = openIds().filter((x) => x !== id);
    const at = Math.max(0, Math.min(ids.length, Math.round(patch.position)));
    ids.splice(at, 0, id);
    renumber(ids);
  }
  return true;
}

// ---------- live updates ----------
// The page keeps one socket open; every write, the owner's from the page
// or the assistant's from a chat, is pushed to it so the page never shows
// a city or a list the assistant just changed.

const sockets = new Set<any>();

function broadcast(payload: any) {
  const msg = JSON.stringify(payload);
  for (const ws of sockets) {
    try { ws.send(msg); } catch { sockets.delete(ws); }
  }
}

// ---------- http ----------

function json(body: any, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json" } });
}

async function readBody(req: Request): Promise<any> {
  try {
    const b = await req.json();
    return b && typeof b === "object" ? b : {};
  } catch {
    return {};
  }
}

Bun.serve({
  port: PORT,
  hostname: "0.0.0.0",
  idleTimeout: 60,
  async fetch(req, server) {
    const url = new URL(req.url);
    const path = url.pathname;
    if (path === "/_health") return json({ ok: true });
    if (path === "/live") {
      if (server.upgrade(req)) return undefined as unknown as Response;
      return new Response("expected a websocket", { status: 400 });
    }

    const v = viewerOf(req);
    const write = req.method !== "GET";
    if (write && !v.canEdit) return json({ error: "this is someone else's page; you can only look" }, 403);

    if (path === "/bootstrap" && req.method === "GET") {
      const settings = readSettings();
      return json({ viewer: v, settings, weather: await weatherFor(settings), todos: todos() });
    }

    if (path === "/settings" && req.method === "GET") return json({ settings: readSettings() });
    if (path === "/settings" && (req.method === "PUT" || req.method === "POST")) {
      const saved = writeSettings(await readBody(req));
      console.log("settings saved by " + v.name + ": " + (saved.city || "no city"));
      const weather = await weatherFor(saved);
      broadcast({ type: "settings", settings: saved, weather });
      return json({ settings: saved, weather });
    }

    if (path === "/geocode" && req.method === "GET") {
      const q = (url.searchParams.get("q") || "").trim().slice(0, 80);
      if (q.length < 2) return json({ results: [] });
      try {
        return json({ results: await geocode(q) });
      } catch (e) {
        console.log("geocode failed: " + e);
        return json({ results: [], error: "the city lookup is not answering right now" });
      }
    }

    if (path === "/weather" && req.method === "GET") {
      return json({ weather: await weatherFor(readSettings(), url.searchParams.get("force") === "1") });
    }

    if (path === "/todos" && req.method === "GET") return json({ todos: todos() });
    if (path === "/todos" && req.method === "POST") {
      const text = String((await readBody(req)).text || "").trim().slice(0, 500);
      if (!text) return json({ error: "nothing to add" }, 400);
      try {
        addTodo(text);
      } catch (e: any) {
        return json({ error: String(e.message || e) }, 400);
      }
      return todosChanged();
    }
    if (path === "/todos" && req.method === "DELETE" && url.searchParams.get("done") === "1") {
      db.query("DELETE FROM todos WHERE done = 1").run();
      return todosChanged();
    }
    const m = path.match(/^\/todos\/(\d+)$/);
    if (m && req.method === "PATCH") {
      if (!patchTodo(Number(m[1]), await readBody(req))) return json({ error: "no such item" }, 404);
      return todosChanged();
    }
    if (m && req.method === "DELETE") {
      db.query("DELETE FROM todos WHERE id = ?").run(Number(m[1]));
      renumber(openIds());
      return todosChanged();
    }

    return json({ error: "not found" }, 404);
  },
  websocket: {
    open(ws) { sockets.add(ws); },
    message() { /* the page writes over HTTP; the socket only pushes */ },
    close(ws) { sockets.delete(ws); },
  },
});

function todosChanged() {
  const list = todos();
  broadcast({ type: "todos", todos: list });
  return json({ todos: list });
}

console.log("home server listening on " + PORT + ", data at " + DATA_DIR);
