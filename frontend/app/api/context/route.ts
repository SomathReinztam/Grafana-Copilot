import { NextResponse } from "next/server";

// Proxy server-side hacia Grafana (evita CORS y mantiene las credenciales fuera del navegador).
// Devuelve el contexto vivo del dashboard: uid, título, rango de tiempo y paneles.
const GRAFANA = process.env.GRAFANA_URL || "http://localhost:3000";
const USER = process.env.GRAFANA_ADMIN_USER || "admin";
const PASS = process.env.GRAFANA_ADMIN_PASSWORD || "admin";
const UID = process.env.DASHBOARD_UID || "copilot-main";

export async function GET() {
  const auth = "Basic " + Buffer.from(`${USER}:${PASS}`).toString("base64");
  try {
    const r = await fetch(`${GRAFANA}/api/dashboards/uid/${UID}`, {
      headers: { Authorization: auth },
      cache: "no-store",
    });
    if (!r.ok) return NextResponse.json({ dashboardUid: UID, panels: [] });
    const d = (await r.json()).dashboard;
    const panels = (d.panels || []).map((p: any) => ({
      id: p.id,
      title: p.title,
      type: p.type,
    }));
    return NextResponse.json({
      dashboardUid: UID,
      title: d.title,
      timeRange: d.time,
      panels,
    });
  } catch {
    return NextResponse.json({ dashboardUid: UID, panels: [] });
  }
}
