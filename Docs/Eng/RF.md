# RF-01: File Ingestion and Normalization (Local ETL)

| Field               | Detail                                                                                                                                                                  |
| ------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Identifier          | RF-01                                                                                                                                                                   |
| Name                | Intelligent Dataset Upload and Cleaning                                                                                                                                 |
| Description         | The system must allow uploading .xlsx and .csv files, removing empty offsets, handling merged cells, and normalizing headers to produce a consistent tabular structure. |
| Actors              | End User, Backend System                                                                                                                                                |
| Priority            | Critical                                                                                                                                                                |
| Preconditions       | File must not be corrupted; size ≤ 10 MB; supported formats (.xlsx, .csv)                                                                                              |
| Postconditions      | Clean dataset structured as a DataFrame; data available in memory or persisted                                                                                          |
| Basic Flow          | 1. Upload file<br />2. Detect first non-null cell<br />3. Remove empty offsets<br />4. Process merged cells<br />5. Normalize column names (snake_case)                 |
| Exceptions          | Empty file (error 422); unsupported format (error 422); read error                                                                                                      |
| Business Rules      | Merged header cells resolved using the primary cell value; at least one valid table must exist                                                                          |
| Acceptance Criteria | Structured JSON returned; no unnamed columns; data consistency ensured                                                                                                  |
| Dependencies        | pandas, openpyxl                                                                                                                                                        |
| Assumptions         | File contains at least one interpretable table                                                                                                                          |

---

# RF-02: Data Structure Analysis and Typing

| Field               | Detail                                                                                                            |
| ------------------- | ----------------------------------------------------------------------------------------------------------------- |
| Identifier          | RF-02                                                                                                             |
| Name                | Schema Detection using AI                                                                                         |
| Description         | The system analyzes the dataset using heuristics and AI models to identify data types and suggest visualizations. |
| Actors              | Backend System, AI Service                                                                                        |
| Priority            | High                                                                                                              |
| Preconditions       | RF-01 completed                                                                                                   |
| Postconditions      | Metadata generated; visualization suggestions available                                                           |
| Basic Flow          | 1. Perform data profiling<br />2. Extract sample<br />3. Send to AI<br />4. Receive JSON with types and charts    |
| Exceptions          | API failure → fallback to heuristics; timeout → fallback                                                        |
| Business Rules      | No sensitive data sent; anonymization if required; AI complements analysis                                        |
| Acceptance Criteria | ≥95% correct column typing; at least 3 valid chart suggestions                                                   |
| Dependencies        | Gemini / OpenAI API                                                                                               |

---

# RF-03: Executive Summary Generation

| Field               | Detail                                                                                                                              |
| ------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| Identifier          | RF-03                                                                                                                               |
| Name                | AI-Based Executive Summary Generation                                                                                               |
| Description         | The system generates a natural language executive summary based on processed data and insights, with fallback between AI providers. |
| Actors              | End User, AI Services                                                                                                               |
| Priority            | High                                                                                                                                |
| Preconditions       | Data processed; insights generated                                                                                                  |
| Postconditions      | Summary available for display and download                                                                                          |
| Basic Flow          | 1. Build context<br />2. Call AI<br />3. Trigger fallback if latency exceeds threshold<br />4. Render summary                       |
| Exceptions          | Timeout → fallback; generation error → controlled message                                                                         |
| Business Rules      | Summary must reflect real data; exportable as PDF                                                                                   |
| Acceptance Criteria | Relevant insights; no contradictions with data                                                                                      |
| Dependencies        | Gemini SDK, OpenAI SDK, ReportLab                                                                                                   |

---

# RF-04: Session Management and Persistence

| Field               | Detail                                                                                                     |
| ------------------- | ---------------------------------------------------------------------------------------------------------- |
| Identifier          | RF-04                                                                                                      |
| Name                | Conditional History and Session Management                                                                 |
| Description         | Enables multiple analysis sessions with persistence conditioned on user registration.                      |
| Actors              | End User                                                                                                   |
| Priority            | Medium                                                                                                     |
| Preconditions       | None                                                                                                       |
| Postconditions      | Chats persisted and linked to user                                                                         |
| Basic Flow          | 1. Start anonymous session<br />2. Attempt new analysis<br />3. Prompt login<br />4. Link sessions to user |
| Exceptions          | No registration → no persistence; session closed → cleanup                                               |
| Business Rules      | Anonymous users limited to one session; persistence requires authentication                                |
| Acceptance Criteria | Previous analyses retrievable; no need to re-upload files                                                  |
| Dependencies        | Supabase Auth, JWT                                                                                         |

---

# RF-05: Interactive Dashboard and Visualization

| Field               | Detail                                                                                             |
| ------------------- | -------------------------------------------------------------------------------------------------- |
| Identifier          | RF-05                                                                                              |
| Name                | Dynamic Dashboard with Filters                                                                     |
| Description         | The system generates an interactive dashboard with dynamic charts that respond to applied filters. |
| Actors              | End User                                                                                           |
| Priority            | High                                                                                               |
| Preconditions       | Data processed                                                                                     |
| Postconditions      | Dashboard rendered                                                                                 |
| Basic Flow          | 1. Generate charts<br />2. User configures layout<br />3. Apply filters<br />4. Real-time updates  |
| Exceptions          | Large dataset → sampling or aggregation                                                           |
| Business Rules      | Charts must follow predefined configurations; filters auto-generated from columns                  |
| Acceptance Criteria | Response time < 200 ms; visual consistency                                                         |
| Dependencies        | VueJS, Chart.js, ApexCharts                                                                        |

---

# RF-06: Data Query Assistant (Q&A)

| Field               | Detail                                                                                                  |
| ------------------- | ------------------------------------------------------------------------------------------------------- |
| Identifier          | RF-06                                                                                                   |
| Name                | Dataset Query Chat                                                                                      |
| Description         | Allows users to query the dataset in natural language, with responses strictly based on available data. |
| Actors              | End User, AI Service                                                                                    |
| Priority            | Medium                                                                                                  |
| Preconditions       | Dataset loaded                                                                                          |
| Postconditions      | Answer generated                                                                                        |
| Basic Flow          | 1. User asks question<br />2. Build context<br />3. Call AI<br />4. Return response                     |
| Exceptions          | Ambiguous query → clarification; AI error → fallback                                                  |
| Business Rules      | Responses must rely only on dataset; no external inference allowed                                      |
| Acceptance Criteria | Accurate responses; no hallucinated data                                                                |
| Dependencies        | LLM API (Gemini / OpenAI)                                                                               |
