# RNF-01: Processing Latency

| Field               | Detail                                                                                                     |
| ------------------- | ---------------------------------------------------------------------------------------------------------- |
| Identifier          | RNF-01                                                                                                     |
| Name                | Processing Latency                                                                                         |
| Description         | The system must process and clean uploaded files efficiently to ensure a responsive user experience.       |
| Category            | Performance                                                                                                |
| Requirement         | The system must process and clean files up to 5 MB in less than 3 seconds, excluding AI API response time. |
| Metric              | Processing time (seconds)                                                                                  |
| Acceptance Criteria | File ≤ 5 MB is processed in < 3 seconds under normal load conditions                                      |
| Dependencies        | pandas, backend processing engine                                                                          |

---

# RNF-02: UI Response Time

| Field               | Detail                                                                                |
| ------------------- | ------------------------------------------------------------------------------------- |
| Identifier          | RNF-02                                                                                |
| Name                | Frontend Response Time                                                                |
| Description         | The system must ensure fast interaction feedback in the dashboard.                    |
| Category            | Performance                                                                           |
| Requirement         | UI visualizations and filters must update in less than 200 ms after user interaction. |
| Metric              | UI latency (milliseconds)                                                             |
| Acceptance Criteria | All filter interactions update charts in < 200 ms                                     |
| Dependencies        | VueJS, client-side processing                                                         |

---

# RNF-03: Concurrency Handling

| Field               | Detail                                                                                                 |
| ------------------- | ------------------------------------------------------------------------------------------------------ |
| Identifier          | RNF-03                                                                                                 |
| Name                | Concurrent Request Handling                                                                            |
| Description         | The backend must support multiple simultaneous users without degradation.                              |
| Category            | Performance                                                                                            |
| Requirement         | The system must handle at least 50 concurrent file processing requests using asynchronous programming. |
| Metric              | Number of concurrent requests                                                                          |
| Acceptance Criteria | System handles ≥ 50 concurrent requests without failure                                               |
| Dependencies        | FastAPI, async/await                                                                                   |

---

# RNF-04: AI Fallback Strategy

| Field               | Detail                                                                                |
| ------------------- | ------------------------------------------------------------------------------------- |
| Identifier          | RNF-04                                                                                |
| Name                | AI Fallback and Resilience                                                            |
| Description         | The system must ensure continuity of AI-based features despite external API failures. |
| Category            | Reliability                                                                           |
| Requirement         | Implement a timeout and fallback mechanism between AI providers.                      |
| Metric              | Failover response time                                                                |
| Acceptance Criteria | If primary AI exceeds 8 seconds, fallback is triggered automatically                  |
| Dependencies        | Gemini API, OpenAI API                                                                |

---

# RNF-05: Volatile Persistence

| Field               | Detail                                                                 |
| ------------------- | ---------------------------------------------------------------------- |
| Identifier          | RNF-05                                                                 |
| Name                | Temporary Data Persistence                                             |
| Description         | The system must manage temporary data for anonymous users efficiently. |
| Category            | Reliability                                                            |
| Requirement         | Data must persist only during session and be deleted after inactivity. |
| Metric              | Data retention time                                                    |
| Acceptance Criteria | Data is deleted after 30 minutes of inactivity                         |
| Dependencies        | Backend session management                                             |

---

# RNF-06: API Key Security

| Field               | Detail                                                                     |
| ------------------- | -------------------------------------------------------------------------- |
| Identifier          | RNF-06                                                                     |
| Name                | API Key Protection                                                         |
| Description         | Sensitive credentials must be securely managed.                            |
| Category            | Security                                                                   |
| Requirement         | API keys must never be exposed in the frontend.                            |
| Metric              | Exposure incidents                                                         |
| Acceptance Criteria | All API calls to LLMs are executed via backend using environment variables |
| Dependencies        | Environment variables, backend architecture                                |

---

# RNF-07: Data Sanitization

| Field               | Detail                                                       |
| ------------------- | ------------------------------------------------------------ |
| Identifier          | RNF-07                                                       |
| Name                | Input Data Sanitization                                      |
| Description         | The system must prevent malicious input from uploaded files. |
| Category            | Security                                                     |
| Requirement         | Validate and sanitize uploaded files before processing.      |
| Metric              | Validation coverage                                          |
| Acceptance Criteria | No execution of embedded scripts or formula injection        |
| Dependencies        | File validation logic, pandas                                |

---

# RNF-08: Conditional Authentication

| Field               | Detail                                              |
| ------------------- | --------------------------------------------------- |
| Identifier          | RNF-08                                              |
| Name                | Secure Access Control                               |
| Description         | Access to user data must be properly restricted.    |
| Category            | Security                                            |
| Requirement         | Only authenticated users can access persisted data. |
| Metric              | Access control validation                           |
| Acceptance Criteria | Users can only access their own datasets            |
| Dependencies        | Supabase Auth, JWT                                  |

---

# RNF-09: Stateless Architecture

| Field               | Detail                                                          |
| ------------------- | --------------------------------------------------------------- |
| Identifier          | RNF-09                                                          |
| Name                | Stateless Backend Design                                        |
| Description         | The backend must be designed for horizontal scalability.        |
| Category            | Maintainability                                                 |
| Requirement         | The system must not store session state locally in the backend. |
| Metric              | Stateless compliance                                            |
| Acceptance Criteria | System can scale horizontally without session conflicts         |
| Dependencies        | Docker, cloud infrastructure                                    |

---

# RNF-10: Observability

| Field               | Detail                                                       |
| ------------------- | ------------------------------------------------------------ |
| Identifier          | RNF-10                                                       |
| Name                | Logging and Monitoring                                       |
| Description         | The system must provide visibility into its operations.      |
| Category            | Maintainability                                              |
| Requirement         | Log critical system events and errors.                       |
| Metric              | Log coverage                                                 |
| Acceptance Criteria | Logs include file processing, AI latency, and parsing errors |
| Dependencies        | Logging framework                                            |

---

# RNF-11: Cross-Platform Compatibility

| Field               | Detail                                                                            |
| ------------------- | --------------------------------------------------------------------------------- |
| Identifier          | RNF-11                                                                            |
| Name                | Multi-Platform Support                                                            |
| Description         | The system must run consistently across environments.                             |
| Category            | Usability / DevOps                                                                |
| Requirement         | The project must be executable on Windows, Linux, and macOS without modification. |
| Metric              | Environment compatibility                                                         |
| Acceptance Criteria | Project runs using standardized dependencies (requirements.txt, package.json)     |
| Dependencies        | Python, Node.js                                                                   |

---

# RNF-12: Continuous Integration

| Field               | Detail                                                           |
| ------------------- | ---------------------------------------------------------------- |
| Identifier          | RNF-12                                                           |
| Name                | CI/CD Pipeline                                                   |
| Description         | The system must ensure code quality through automated pipelines. |
| Category            | DevOps                                                           |
| Requirement         | Implement CI pipeline with automated testing before deployment.  |
| Metric              | Pipeline success rate                                            |
| Acceptance Criteria | Tests executed automatically before deployment                   |
| Dependencies        | GitHub Actions, deployment platform                              |

---

# Quality Attributes Summary

| Attribute   | Objective                            | Key Tool                                 |
| ----------- | ------------------------------------ | ---------------------------------------- |
| Portability | Run on any OS                        | Docker / virtual environments            |
| Robustness  | Avoid system failure on AI errors    | Fallback logic                           |
| Privacy     | Protect user data                    | JWT / session cleanup                    |
| Performance | Fast data processing and UI response | Client-side rendering, optimized backend |
