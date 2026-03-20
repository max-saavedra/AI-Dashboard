<template>
  <div class="home">
    <!-- Background mesh -->
    <div class="home__mesh" aria-hidden="true">
      <div class="mesh-orb mesh-orb--1" />
      <div class="mesh-orb mesh-orb--2" />
      <div class="mesh-grid" />
    </div>

    <!-- Nav -->
    <nav class="home__nav">
      <div class="nav-logo">
        <span class="logo-mark">N</span>
        <span class="logo-text">eo</span>
      </div>
      <div class="nav-actions">
        <button class="btn btn--ghost" @click="$router.push('/auth')">Sign in</button>
        <button class="btn btn--primary" @click="$router.push('/workspace')">
          Try free
        </button>
      </div>
    </nav>

    <!-- Hero -->
    <main class="home__hero">
      <div class="hero__badge">
        <span class="badge-dot" />
        AI-Powered Data Intelligence
      </div>

      <h1 class="hero__title">
        Your data.<br />
        <span class="hero__title-accent">Understood.</span>
      </h1>

      <p class="hero__sub">
        Upload any Excel or CSV file. Neo analyses, visualises, and explains
        your data through interactive dashboards and AI-generated insights —
        in seconds.
      </p>

      <div class="hero__cta">
        <button class="btn btn--primary btn--lg" @click="$router.push('/workspace')">
          <svg viewBox="0 0 20 20" fill="currentColor" width="18" height="18">
            <path d="M9.707 1.293a1 1 0 00-1.414 0L1.586 8 0 9.586l10 10 10-10L18.414 8l-6.707-6.707zM10 17.172L2.828 10 10 2.828 17.172 10 10 17.172z"/>
          </svg>
          Start analysing — it's free
        </button>
        <span class="hero__cta-note">No account required for first analysis</span>
      </div>

      <!-- Feature pills -->
      <div class="hero__features">
        <div v-for="f in features" :key="f.label" class="feature-pill">
          <span class="feature-pill__icon">{{ f.icon }}</span>
          {{ f.label }}
        </div>
      </div>
    </main>

    <!-- How it works -->
    <section class="home__steps">
      <h2 class="steps__title">How Neo works</h2>
      <div class="steps__grid">
        <div v-for="(step, i) in steps" :key="i" class="step-card">
          <div class="step-card__num mono">0{{ i + 1 }}</div>
          <div class="step-card__icon">{{ step.icon }}</div>
          <h3 class="step-card__title">{{ step.title }}</h3>
          <p class="step-card__desc">{{ step.desc }}</p>
        </div>
      </div>
    </section>

    <!-- Footer -->
    <footer class="home__footer">
      <span class="logo-mark small">N</span>
      <span class="text-dim">Neo Analytics · Built with AI</span>
    </footer>
  </div>
</template>

<script setup>
const features = [
  { icon: '⚡', label: 'Instant ETL' },
  { icon: '🤖', label: 'AI Schema Detection' },
  { icon: '📊', label: 'Interactive Charts' },
  { icon: '📝', label: 'Executive Summaries' },
  { icon: '💬', label: 'Data Q&A Chat' },
  { icon: '📄', label: 'PDF Export' }
]

const steps = [
  {
    icon: '📁',
    title: 'Upload your file',
    desc: 'Drop an Excel or CSV file. Neo handles messy headers, merged cells, and empty rows automatically.'
  },
  {
    icon: '🧠',
    title: 'AI analyses structure',
    desc: 'Gemini reads your schema, identifies column types, and suggests the most meaningful visualisations.'
  },
  {
    icon: '📈',
    title: 'Interact with your dashboard',
    desc: 'Apply filters, toggle charts, and explore your data through a Power BI-style interactive view.'
  },
  {
    icon: '📋',
    title: 'Generate executive summary',
    desc: 'One click produces a professional summary with key insights, trends, and recommendations.'
  }
]
</script>

<style scoped>
/* ── Layout ──────────────────────────────────────────────── */
.home {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  position: relative;
  overflow: hidden;
}

/* ── Background ──────────────────────────────────────────── */
.home__mesh {
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 0;
}
.mesh-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.12;
}
.mesh-orb--1 {
  width: 600px; height: 600px;
  background: radial-gradient(circle, #2563EB, transparent 70%);
  top: -200px; left: -100px;
}
.mesh-orb--2 {
  width: 400px; height: 400px;
  background: radial-gradient(circle, #1D4ED8, transparent 70%);
  bottom: -100px; right: -50px;
}
.mesh-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(37,99,235,0.04) 1px, transparent 1px),
    linear-gradient(90deg, rgba(37,99,235,0.04) 1px, transparent 1px);
  background-size: 48px 48px;
}

/* ── Nav ─────────────────────────────────────────────────── */
.home__nav {
  position: relative;
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 48px;
  border-bottom: 1px solid var(--col-border);
}
.nav-logo {
  display: flex;
  align-items: baseline;
  gap: 0;
}
.logo-mark {
  font-family: var(--font-mono);
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--col-blue-400);
  background: linear-gradient(135deg, #60A5FA, #2563EB);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
.logo-mark.small { font-size: 1rem; margin-right: 6px; }
.logo-text {
  font-family: var(--font-display);
  font-size: 1.5rem;
  font-weight: 800;
  color: var(--col-text-primary);
}
.nav-actions { display: flex; gap: 12px; align-items: center; }

/* ── Hero ────────────────────────────────────────────────── */
.home__hero {
  position: relative;
  z-index: 10;
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 24px 60px;
  text-align: center;
  max-width: 760px;
  margin: 0 auto;
}
.hero__badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: rgba(37,99,235,0.12);
  border: 1px solid rgba(37,99,235,0.3);
  border-radius: var(--radius-full);
  padding: 6px 16px;
  font-size: 0.8rem;
  font-family: var(--font-mono);
  color: var(--col-blue-400);
  letter-spacing: 0.05em;
  margin-bottom: 32px;
  animation: fadeIn 0.6s ease both;
}
.badge-dot {
  width: 6px; height: 6px;
  background: var(--col-blue-400);
  border-radius: 50%;
  animation: pulse-glow 2s infinite;
}
.hero__title {
  font-size: clamp(2.8rem, 7vw, 5rem);
  font-weight: 800;
  line-height: 1.05;
  letter-spacing: -0.03em;
  color: var(--col-text-primary);
  animation: fadeIn 0.6s 0.1s ease both;
}
.hero__title-accent {
  background: linear-gradient(135deg, #60A5FA 0%, #2563EB 50%, #1D4ED8 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
.hero__sub {
  margin-top: 20px;
  font-size: 1.1rem;
  line-height: 1.7;
  color: var(--col-text-secondary);
  max-width: 560px;
  animation: fadeIn 0.6s 0.2s ease both;
}
.hero__cta {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  margin-top: 36px;
  animation: fadeIn 0.6s 0.3s ease both;
}
.hero__cta-note {
  font-size: 0.78rem;
  color: var(--col-text-dim);
  font-family: var(--font-mono);
}
.hero__features {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 10px;
  margin-top: 48px;
  animation: fadeIn 0.6s 0.4s ease both;
}
.feature-pill {
  display: flex;
  align-items: center;
  gap: 6px;
  background: var(--col-surface);
  border: 1px solid var(--col-border);
  border-radius: var(--radius-full);
  padding: 6px 14px;
  font-size: 0.82rem;
  color: var(--col-text-secondary);
  transition: border-color var(--t-fast), color var(--t-fast);
}
.feature-pill:hover {
  border-color: var(--col-blue-600);
  color: var(--col-text-primary);
}
.feature-pill__icon { font-size: 0.9rem; }

/* ── Steps ───────────────────────────────────────────────── */
.home__steps {
  position: relative;
  z-index: 10;
  padding: 64px 48px;
  border-top: 1px solid var(--col-border);
}
.steps__title {
  text-align: center;
  font-size: 1.6rem;
  margin-bottom: 40px;
  color: var(--col-text-primary);
}
.steps__grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 20px;
  max-width: 960px;
  margin: 0 auto;
}
.step-card {
  background: var(--col-surface);
  border: 1px solid var(--col-border);
  border-radius: var(--radius-lg);
  padding: 24px;
  transition: border-color var(--t-normal), transform var(--t-normal);
}
.step-card:hover {
  border-color: var(--col-blue-600);
  transform: translateY(-2px);
}
.step-card__num {
  font-size: 0.7rem;
  color: var(--col-blue-400);
  letter-spacing: 0.1em;
  margin-bottom: 12px;
}
.step-card__icon { font-size: 1.5rem; margin-bottom: 10px; }
.step-card__title {
  font-size: 0.95rem;
  font-weight: 600;
  margin-bottom: 8px;
  color: var(--col-text-primary);
}
.step-card__desc {
  font-size: 0.85rem;
  line-height: 1.6;
  color: var(--col-text-secondary);
}

/* ── Footer ──────────────────────────────────────────────── */
.home__footer {
  position: relative;
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 20px;
  border-top: 1px solid var(--col-border);
  font-size: 0.82rem;
}

/* ── Buttons ─────────────────────────────────────────────── */
.btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 9px 20px;
  border-radius: var(--radius-md);
  font-size: 0.88rem;
  font-weight: 500;
  font-family: var(--font-body);
  cursor: pointer;
  border: none;
  transition: all var(--t-fast);
}
.btn--ghost {
  background: transparent;
  color: var(--col-text-secondary);
  border: 1px solid var(--col-border);
}
.btn--ghost:hover {
  color: var(--col-text-primary);
  border-color: var(--col-blue-600);
}
.btn--primary {
  background: var(--col-blue-600);
  color: white;
  box-shadow: 0 0 20px rgba(37,99,235,0.3);
}
.btn--primary:hover {
  background: var(--col-blue-700);
  box-shadow: 0 0 28px rgba(37,99,235,0.4);
}
.btn--lg { padding: 13px 28px; font-size: 1rem; }
</style>
