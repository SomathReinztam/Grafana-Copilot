FROM node:20-slim

WORKDIR /app

COPY package*.json ./
RUN npm install --no-audit --no-fund

COPY . .

# NEXT_PUBLIC_* se hornean en el build (las usa el navegador → localhost)
ARG NEXT_PUBLIC_GRAFANA_URL=http://localhost:3000
ARG NEXT_PUBLIC_DASHBOARD_UID=copilot-main
ARG NEXT_PUBLIC_AGUI_URL=http://localhost:8000/agui
ENV NEXT_PUBLIC_GRAFANA_URL=$NEXT_PUBLIC_GRAFANA_URL
ENV NEXT_PUBLIC_DASHBOARD_UID=$NEXT_PUBLIC_DASHBOARD_UID
ENV NEXT_PUBLIC_AGUI_URL=$NEXT_PUBLIC_AGUI_URL

RUN npm run build

EXPOSE 3001
CMD ["npx", "next", "start", "-p", "3001"]
