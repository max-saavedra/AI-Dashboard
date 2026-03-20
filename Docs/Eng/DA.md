
# Data Architecture – IA Dashboard

## 1. Data Flow Diagram (Data Pipeline)

The data lifecycle is structured into four key stages:

1. **Ingestion**
2. **Processing & Normalization**
3. **Enrichment (AI)**
4. **Persistence & Consumption**

This pipeline ensures a continuous transformation from raw input to actionable insights.

---

## 2. Data Architecture Layers

### 2.1 Ingestion Layer (Raw Layer)

**Source:**

- Binary files (`.xlsx`, `.csv`) uploaded via `multipart/form-data`

**Processing Strategy:**

- Files are loaded into memory in the backend (FastAPI) using `BytesIO`
- For production-scale scenarios:
  - Files should be uploaded to **Google Cloud Storage**
  - Processing should be handled asynchronously

**Key Characteristics:**

- Ephemeral data handling
- Minimal preprocessing
- Input validation and sanitization

---

### 2.2 Processing & Normalization Layer (Silver Layer)

This layer is responsible for transforming raw data into a structured and analyzable format.

#### Offset Detection

- A **data density heuristic** is applied
- If the first *N* rows contain more than 80% null values:
  - They are discarded
  - The system identifies the true header row

#### Schema Normalization

- A **Schema Agent (Gemini 1.5 Flash)** is used
- A sample of the dataset is analyzed
- The AI returns structured metadata:

Example:

- Column: `Vta_2024` → Type: `Float`, Alias: `Ventas 2024`

#### Merged Cells Handling

- Implemented using **Pandas Forward Fill (`ffill`)**
- Ensures each row contains complete contextual information

#### Output

- Clean, normalized DataFrame
- Consistent column naming (snake_case)
- Typed dataset ready for analytics

---

### 2.3 Enrichment & Insights Layer (Gold Layer)

This layer transforms structured data into business insights.

#### Dynamic Aggregations

- KPI calculations:
  - Averages
  - Maximums / minimums
  - Trends over time

#### AI Contextualization

- The system does NOT send the full dataset to the LLM
- Instead, it sends:
  - Aggregated metrics
  - User-selected tags
  - Structured summaries

#### Benefits

- Reduced token usage
- Lower operational costs
- Faster response times
- Deterministic control over data interpretation

#### Output

- Executive summary
- Key insights
- Structured analytical metadata

---

## 3. Data Model (Database Design)

The system uses **PostgreSQL (via Supabase)**, combining relational modeling with **JSONB** for flexibility.

---

### Table: `users` (Managed by Supabase Auth)

| Column | Type      | Description            |
| ------ | --------- | ---------------------- |
| id     | UUID (PK) | Unique user identifier |
| email  | String    | User email             |

---

### Table: `chats` (Analysis Threads)

| Column     | Type      | Description                                      |
| ---------- | --------- | ------------------------------------------------ |
| id         | UUID (PK) | Unique chat identifier                           |
| user_id    | UUID (FK) | Reference to user (nullable for anonymous users) |
| name       | String    | Chat name (e.g., "March Sales")                  |
| created_at | Timestamp | Creation timestamp                               |

---

### Table: `dashboards` (Core Data Entity)

| Column       | Type      | Description                       |
| ------------ | --------- | --------------------------------- |
| id           | UUID (PK) | Unique identifier                 |
| chat_id      | UUID (FK) | Reference to chat                 |
| cleaned_data | JSONB     | Cleaned dataset in JSON format    |
| ai_insights  | JSONB     | AI-generated insights and summary |
| chart_config | JSONB     | Visualization configuration       |
| metadata     | JSONB     | File metadata, tags, schema info  |

---

## 4. Data Persistence Strategy & Lifecycle

### 4.1 Anonymous Data Handling

- Stored with `user_id = NULL`
- Automatically deleted using a scheduled job:

```sql
DELETE FROM dashboards
WHERE user_id IS NULL
AND created_at < NOW() - INTERVAL '24 hours';
```


---

### 4.2 Data Security

* **Row Level Security (RLS)** enforced in Supabase
* Ensures:
  * Users can only access their own data
  * Full isolation between tenants
* Aligns with:
  * Privacy standards
  * Ethical data handling principles (BCorp alignment)

---

### 4.3 Performance Strategy

* Processed data is sent once to the frontend
* All filtering operations are executed client-side:
  * VueJS reactive filtering
  * No additional backend calls required

**Benefits:**

* Reduced latency
* Improved UX responsiveness
* Lower backend load

---

## 5. Initial Backend ETL Backlog

To bootstrap the system, the following tasks are prioritized:

### Task 1: File Upload Handling

* Configure FastAPI with `python-multipart`
* Enable file ingestion endpoints

---

### Task 2: Excel Cleaning Service

* Implement `ExcelCleaner` service using Pandas
* Remove empty rows using threshold-based `dropna`
* Detect data start dynamically

---

### Task 3: Schema Detection Prompt

* Design system prompt for Gemini
* Input: `df.head()`
* Output: structured JSON with:
  * Column types
  * Aliases
  * Suggested roles

---

### Task 4: Analysis Endpoint

* Implement `POST /analyze`
* Orchestrate:
  * File ingestion
  * Data cleaning
  * Schema detection
  * AI enrichment

---

## 6. Conclusion

This data architecture enables:

* Transformation of unstructured data into structured insights
* Efficient use of AI through controlled enrichment
* Scalable and flexible storage with JSONB
* High-performance analytics with minimal latency

It establishes a strong foundation for:

* Advanced analytics pipelines
* Real-time data processing
* AI-driven decision systems
