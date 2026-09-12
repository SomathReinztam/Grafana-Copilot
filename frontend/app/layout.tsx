import type { Metadata } from "next";
import "./globals.css";
import "@copilotkit/react-ui/styles.css";
import { Providers } from "./providers";

export const metadata: Metadata = {
  title: "Grafana Copilot",
  description: "Agente que construye y edita dashboards de Grafana sobre Postgres",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="es">
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
