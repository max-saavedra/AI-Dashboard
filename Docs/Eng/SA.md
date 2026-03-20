# System Architecture – IA Dashboard

## 1. System Architecture Diagram

The following diagram illustrates the logical architecture of the system, including its main layers, data flows, and orchestration between frontend, backend, data services, and AI services.

![System Architecture](Docs/Img/Architecture.png)

---

## 2. Architecture Overview

The architecture follows a **stateless N-tier model**, enabling:

- Efficient horizontal scalability
- Simplified CI/CD deployment
- High availability and fault tolerance
- Clear separation of concerns

The design aligns with key principles:

- **Cloud-Native Architecture**
- **Resilience (Fault Tolerance)**
- **Observability**
- **Security by Design**

---

## 3. Architecture Layers

### 3.1 Presentation Layer (Frontend)

**Technology:**

- Vue 3 (Composition API)
- Vite (build tool)

**Key Components:**

- Single Page Application (SPA)
- State management with Pinia
- Chart rendering using ApexCharts

**Responsibilities:**

- User interaction
- Dashboard rendering
- Filter and UI state management
- API consumption

**Technical Characteristics:**

- Fully client-side rendering
- Highly reactive UI (Power BI-like experience)
- Reduced backend load

**Deployment:**

- Vercel / Netlify (edge delivery)

---

### 3.2 Application Layer (Backend)

**Technology:**

- Python 3.11+
- FastAPI (asynchronous)

**Internal Architecture:**

#### a. API Layer

- REST endpoints (`/upload`, `/analyze`, `/summary`)
- Request validation using Pydantic

#### b. ETL Engine (PandasETL)

Responsibilities:

- Excel/CSV file ingestion
- Automatic structure detection (offset detection)
- Data cleaning and normalization
- Structured DataFrame generation

#### c. AI Orchestrator (AIOrchestrator)

Implemented pattern:

- **Strategy + Fallback**

Flow:

1. Primary call to Google Gemini
2. Configurable timeout (8 seconds)
3. Automatic fallback to OpenAI

**Benefits:**

- High availability of AI services
- Reduced perceived latency
- Vendor independence

**Deployment:**

- Docker container
- GCP Cloud Run (serverless)

**Advantages:**

- Auto-scaling
- Pay-per-use model
- Native async concurrency

---

### 3.3 Data and Persistence Layer

**Database:**

- PostgreSQL (managed via Supabase)

**Data Model:**

- Users
- Chats
- Dashboards
- Analytical results (JSONB)

**Why JSONB:**

- Flexible schema for dynamic data
- Ideal for dashboard configurations
- Supports hybrid querying (relational + semi-structured)

---

### 3.4 Authentication and Authorization

**Technology:**

- Supabase Auth

**Mechanism:**

- JWT (JSON Web Tokens)

**Flow:**

1. User authenticates via frontend
2. Supabase issues JWT
3. Frontend attaches JWT to API requests
4. Backend validates access control

**Characteristics:**

- Stateless security model
- Scalable authentication
- Direct frontend integration

---

### 3.5 Artificial Intelligence Layer

**Providers:**

- Google Gemini 1.5 Flash (primary)
- OpenAI API (fallback)

**Responsibilities:**

- Schema detection (column typing)
- Insight generation
- Executive summary generation
- Natural language data querying (Q&A)

**Strategy:**

- AI as a value-added layer (not core logic)
- Backend maintains deterministic control

---

## 4. Communication Flows

### 4.1 User → Frontend

- Protocol: HTTPS (TLS 1.3)
- Interaction via UI

---

### 4.2 Frontend → Backend

- Protocol: REST API over HTTPS
- Format: JSON
- Authentication: JWT

---

### 4.3 Backend → AI Services

- Gemini: gRPC / REST
- OpenAI: HTTPS
- Security: Environment variables

---

### 4.4 Backend → Database

- Protocol: Secure SQL connection
- Operations: CRUD + analytical storage

---

## 5. Key Architectural Principles

### 5.1 Stateless Architecture

- No session state stored in backend
- Enables horizontal scaling

---

### 5.2 Separation of Concerns

- Frontend: UI/UX
- Backend: business logic and orchestration
- AI: insight generation
- Database: persistence

---

### 5.3 Resilience

- AI fallback strategy
- Controlled error handling
- Defined timeouts

---

### 5.4 Performance Optimization

- Client-side processing for visualizations
- Asynchronous backend
- Reduced external calls

---

### 5.5 Security

- API keys secured in backend
- JWT-based authentication
- File sanitization
- Encrypted communication

---

## 6. Conclusion

This architecture is designed to:

- Scale horizontally with minimal friction
- Integrate efficiently with AI services
- Deliver high frontend performance
- Ensure security and resilience

It also provides a strong foundation for future evolution, including:

- Migration to microservices
- Advanced data pipelines
- Integration with external BI tools
- Adoption of more advanced AI models

---
