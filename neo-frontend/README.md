# Neo – Frontend

Vue 3 SPA for the Neo intelligent analytics platform.

## Stack

- Vue 3 (Composition API)
- Vite 5
- Pinia (state management)
- Vue Router 4
- ApexCharts (via vue3-apexcharts)
- Axios

## Design

- Typefaces: Syne (display), DM Sans (body), Space Mono (code/mono)
- Palette: Deep navy `#070B14` base · Electric blue `#2563EB` accent · Cold white text
- Style: Minimalist dark UI inspired by Claude / Gemini — but distinctly blue-black

## Local Setup

```bash
npm install
cp .env.example .env
npm run dev
# → http://localhost:5173
```

The Vite dev server proxies `/api` to `http://localhost:8000` (the FastAPI backend).

## Project Structure

```
src/
  views/
    HomeView.vue          Landing / intro page
    WorkspaceView.vue     Main chat-style workspace (sidebar + content)
    DashboardView.vue     Standalone full-page dashboard
    AuthView.vue          Sign in / sign up

  components/
    chat/
      UploadWizard.vue    Multi-step file upload + user context form
      ProcessingScreen.vue  Animated ETL+AI loading state
    dashboard/
      DashboardPanel.vue  Main dashboard: header, filters, KPIs, charts, chat
      ChartCard.vue       Individual ApexChart card with info overlay
      DataChat.vue        Collapsible Q&A mini-chat grounded in dataset
      SummaryModal.vue    Executive summary generation + PDF download
    ui/
      Icon*.vue           SVG icon components

  stores/
    auth.js               Authentication state (JWT + user)
    workspace.js          Sessions, analysis results, Q&A, filters

  services/
    api.js                Axios instance + typed API methods

  composables/
    useChartFilters.js    Reactive client-side chart filtering

  assets/
    main.css              Global design tokens + utility classes
```

## User Flow

1. **Landing** (`/`) – intro, "Try free" → workspace
2. **Upload wizard** – drop file, set role/objective/tags, submit
3. **Processing** – animated progress while backend runs ETL + AI
4. **Dashboard** – KPI cards, 3+ ApexCharts, filter bar, chart picker
5. **Data Chat** – collapsible Q&A panel at the bottom
6. **Summary** – modal with optional custom structure → generate → PDF download
7. **Sessions** – sidebar lists saved chats; requires sign-in to persist
