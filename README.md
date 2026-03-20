
# 🚀 AI - Dashboard: Enterprise Data Intelligence

**AI-Dashboard** es una plataforma Full-Stack de analítica avanzada que transforma archivos de datos (Excel/CSV) en tableros dinámicos mediante el poder de la  **IA Generativa** . El sistema automatiza la limpieza de datos (ETL) y genera visualizaciones estratégicas basadas en lenguaje natural.

---

## 🏛️ Arquitectura del Sistema

El proyecto emplea una arquitectura de  **Microservicios Desacoplados** , diseñada para ser resiliente y escalable en entornos de nube:

* **Frontend:** Aplicación SPA desarrollada con  **VueJS 3** , desplegada de forma estática en  **GitHub Pages** .
* **Backend:** API REST robusta construida con  **FastAPI (Python 3.11)** , orquestada con **Docker Compose** y desplegada en  **Google Cloud Platform (Compute Engine)** .
* **Base de Datos:** Persistencia asíncrona mediante **PostgreSQL** alojado en  **Supabase** .
* **Capa de IA:** Orquestación inteligente con **Google Gemini 1.5 Flash** (primario) y **OpenAI** (fallback), garantizando un procesamiento ininterrumpido.

> [!TIP]
>
> Puedes consultar los diagramas de arquitectura y flujo de datos detallados en la carpeta `/Docs/Spa/SA.md`.

---

## 🤖 Implementación de IA

## 1. En el Núcleo de la App (Core)

* **Limpieza de Datos Inteligente:** Uso de LLMs para normalizar formatos, detectar tipos de datos y sugerir correcciones en datasets sucios.
* **Insights Generativos:** Traducción de métricas crudas a resúmenes ejecutivos comprensibles.
* **Análisis Predictivo:** Identificación de tendencias basada en la data histórica cargada por el usuario.

## 2. En el Flujo de Desarrollo (DevOps)

* **Optimización de Código:** Uso de IA para la refactorización de lógica asíncrona y resolución de errores de concurrencia (`greenlet`).
* **Automatización de Infraestructura:** Generación asistida de configuraciones para  **Docker** ,**Nginx** y reglas de Firewall en  **GCP** .

---

## 🛠️ Guía de Ejecución en Local

## 📋 Requisitos Previos

* **Python 3.11+**
* **Node.js 18+**
* **Docker & Docker Compose** (Opcional para Backend)

## 1. Clonar el Proyecto

**Bash**

```
git clone https://github.com/max-saavedra/AI-Dashboard.git
cd AI-Dashboard
```

## 2. Levantar el Backend (FastAPI)

Existen dos formas de ejecutarlo:

**A. Mediante Docker (Recomendado):**

**Bash**

```
cd ia-dashboard-backend
cp .env.example .env  # Configurar SUPABASE_URL y GEMINI_API_KEY
docker compose up -d --build
```

**B. Ejecución Manual (Entorno Virtual):**

**Bash**

```
cd ia-dashboard-backend
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## 3. Levantar el Frontend (VueJS)

**Bash**

```
cd ../neo-frontend
npm install
# Asegúrate de que .env apunte a http://localhost:8000
npm run dev
```

*Accede a: `http://localhost:5173`*

---

## 📂 Documentación del Proyecto

El repositorio incluye documentación técnica completa en español dentro de la carpeta `/Docs/Spa`:

| **Documento**                                      | **Descripción**                                    |
| -------------------------------------------------------- | --------------------------------------------------------- |
| [AD.md](https://www.google.com/search?q=./Docs/Spa/AD.md)   | Arquitectura de Datos y modelo de Entidad-Relación.      |
| [SA.md](https://www.google.com/search?q=./Docs/Spa/SA.md)   | Arquitectura del Sistema (Cloud & Local).                 |
| [RF.md](https://www.google.com/search?q=./Docs/Spa/RF.md)   | Requerimientos Funcionales detallados.                    |
| [RNF.md](https://www.google.com/search?q=./Docs/Spa/RNF.md) | Requerimientos No Funcionales (Seguridad, Escalabilidad). |
| [UC.md](https://www.google.com/search?q=./Docs/Spa/UC.md)   | Casos de Uso del sistema.                                 |
| [US.md](https://www.google.com/search?q=./Docs/Spa/US.md)   | Historias de Usuario (User Stories).                      |

---

## 👤 Perfil del Autor: Max Saavedra

**Software Engineer | Cloud & AI Specialist**

* **Educación:** Universidad Nacional Mayor de San Marcos (UNMSM).
* **Certificaciones:** HCIA-AI, HCIA-Cloud Computing, HCIA-5G (Huawei ICT Competition).
