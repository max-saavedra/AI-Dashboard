# Arquitectura del Sistema – IA Dashboard

## 1. Diagrama de Arquitectura del Sistema

El siguiente diagrama representa la arquitectura lógica del sistema, incluyendo las capas principales, flujos de datos y la orquestación entre frontend, backend, servicios de datos y servicios de inteligencia artificial.

![Arquitectura del Sistema](Docs/Img/Architecture.png)

---

## 2. Descripción de la Arquitectura

La arquitectura adoptada sigue un modelo de **N-Capas Stateless (sin estado)**, lo que permite:

- Escalabilidad horizontal eficiente
- Despliegue continuo (CI/CD) simplificado
- Alta disponibilidad y tolerancia a fallos
- Separación clara de responsabilidades

El diseño está alineado con principios de:

- **Cloud-Native Architecture**
- **Resiliencia (Fault Tolerance)**
- **Observabilidad**
- **Seguridad por diseño (Security by Design)**

---

## 3. Capas de la Arquitectura

### 3.1 Capa de Presentación (Frontend)

**Tecnología:**

- Vue 3 (Composition API)
- Vite (build tool)

**Componentes clave:**

- SPA (Single Page Application)
- Gestión de estado con Pinia
- Renderizado de gráficos con ApexCharts

**Responsabilidades:**

- Interacción con el usuario
- Renderizado del dashboard
- Gestión de filtros y estado UI
- Consumo de APIs REST

**Características técnicas:**

- Renderizado completamente en cliente (client-side rendering)
- Alta reactividad (UX tipo Power BI)
- Minimización de llamadas al backend

**Despliegue:**

- Vercel / Netlify (Edge delivery)

---

### 3.2 Capa de Aplicación (Backend)

**Tecnología:**

- Python 3.11+
- FastAPI (asíncrono)

**Arquitectura interna:**

#### a. API Layer

- Endpoints REST (`/upload`, `/analyze`, `/summary`)
- Validación con Pydantic

#### b. Motor ETL (PandasETL)

Responsabilidades:

- Lectura de archivos Excel/CSV
- Detección automática de estructura (offset)
- Limpieza y normalización de datos
- Generación de DataFrame estructurado

#### c. Orquestador de IA (AIOrchestrator)

Patrón implementado:

- **Strategy + Fallback**

Flujo:

1. Llamada a Google Gemini (prioritario)
2. Timeout configurable (8s)
3. Fallback automático a OpenAI

**Ventajas:**

- Alta disponibilidad de IA
- Reducción de latencia percibida
- Independencia de proveedor

**Despliegue:**

- Docker container
- GCP Cloud Run (serverless)

**Beneficios:**

- Escalado automático
- Pago por uso
- Concurrencia asíncrona

---

### 3.3 Capa de Datos y Persistencia

**Base de Datos:**

- PostgreSQL (gestionado por Supabase)

**Modelo de Datos:**

- Usuarios
- Chats
- Dashboards
- Resultados analíticos (JSONB)

**Ventajas del uso de JSONB:**

- Flexibilidad en estructuras dinámicas
- Ideal para configuraciones de dashboards
- Permite consultas híbridas (relacional + semi-estructurado)

---

### 3.4 Autenticación y Autorización

**Tecnología:**

- Supabase Auth

**Mecanismo:**

- JWT (JSON Web Tokens)

**Flujo:**

1. Usuario se autentica desde frontend
2. Supabase emite JWT
3. Frontend envía JWT en headers al backend
4. Backend valida acceso a recursos

**Características:**

- Seguridad stateless
- Escalable
- Integración directa con frontend

---

### 3.5 Capa de Inteligencia Artificial

**Proveedores:**

- Google Gemini 1.5 Flash (principal)
- OpenAI API (fallback)

**Responsabilidades:**

- Detección de schema (tipado de columnas)
- Generación de insights
- Generación de resumen ejecutivo
- Soporte para consultas Q&A

**Estrategia:**

- IA como capa de valor (no core lógico)
- Backend mantiene control determinístico

---

## 4. Flujos de Comunicación

### 4.1 Usuario → Frontend

- Protocolo: HTTPS (TLS 1.3)
- Interacción: UI/UX

---

### 4.2 Frontend → Backend

- Protocolo: REST API (HTTPS)
- Formato: JSON
- Autenticación: JWT

---

### 4.3 Backend → IA Services

- Gemini: gRPC / REST
- OpenAI: HTTPS
- Seguridad: Variables de entorno

---

### 4.4 Backend → Base de Datos

- Protocolo: SQL sobre conexión segura
- Operaciones: CRUD + almacenamiento analítico

---

## 5. Principios Arquitectónicos Clave

### 5.1 Stateless Architecture

- No almacenamiento de sesión en backend
- Permite escalabilidad horizontal

---

### 5.2 Separation of Concerns

- Frontend: UI/UX
- Backend: lógica y orquestación
- IA: generación de valor
- DB: persistencia

---

### 5.3 Resiliencia

- Fallback de IA
- Manejo de errores controlado
- Timeouts definidos

---

### 5.4 Performance Optimization

- Procesamiento en cliente (gráficos)
- Backend asíncrono
- Minimización de llamadas externas

---

### 5.5 Seguridad

- API Keys protegidas (backend)
- JWT para autenticación
- Sanitización de archivos
- Encriptación en tránsito

---

## 6. Conclusión

Esta arquitectura está diseñada para:

- Escalar horizontalmente sin fricción
- Integrarse eficientemente con servicios de IA
- Mantener alta performance en frontend
- Garantizar seguridad y resiliencia

Además, permite evolucionar fácilmente hacia:

- Microservicios
- Data pipelines más complejos
- Integración con herramientas BI externas
- Modelos de IA más avanzados

---
