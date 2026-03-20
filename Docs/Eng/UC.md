# Use Cases

## UC-01: Intelligent Data Upload and Processing

| Field             | Detail                                                                                                                                                                                       |
| ----------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Identifier        | UC-01                                                                                                                                                                                        |
| Name              | Intelligent Data Upload and Processing                                                                                                                                                       |
| Primary Actor     | User                                                                                                                                                                                         |
| Description       | Allows the user to upload an Excel/CSV file with an unstructured format to be cleaned and transformed into a structured dataset.                                                             |
| Preconditions     | Valid file available for upload                                                                                                                                                              |
| Postconditions    | Clean dataset ready for analysis and visualization                                                                                                                                           |
| Main Flow         | 1. User uploads file2. System detects empty offsets using heuristics3. A sample is analyzed with AI to validate column names and types4. System normalizes data5. Data is temporarily stored |
| Alternative Flows | Invalid file → validation errorProcessing error → controlled failure message                                                                                                               |
| Business Rules    | The system must preserve original data integrity                                                                                                                                             |
| Priority          | High                                                                                                                                                                                         |

---

## UC-02: Dashboard and Executive Summary Generation

| Field             | Detail                                                                                                                                     |
| ----------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| Identifier        | UC-02                                                                                                                                      |
| Name              | Dashboard and Executive Summary Generation                                                                                                 |
| Primary Actor     | User                                                                                                                                       |
| Secondary Actors  | AI Services                                                                                                                                |
| Description       | Transforms tabular data into interactive visualizations and an AI-generated executive summary.                                             |
| Preconditions     | Processed data available                                                                                                                   |
| Postconditions    | Dashboard rendered and summary generated                                                                                                   |
| Main Flow         | 1. System maps columns to chart types2. User selects context (tags)3. System requests summary from AI4. Dashboard and summary are rendered |
| Alternative Flows | AI timeout → fallback to secondary provider                                                                                               |
| Business Rules    | Charts must follow predefined configurations                                                                                               |
| Priority          | High                                                                                                                                       |

---

## UC-03: Analysis History Management

| Field             | Detail                                                                                                                              |
| ----------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| Identifier        | UC-03                                                                                                                               |
| Name              | Analysis History Management                                                                                                         |
| Primary Actor     | Registered User                                                                                                                     |
| Description       | Allows users to store and retrieve previous analyses.                                                                               |
| Preconditions     | User authenticated (for persistence)                                                                                                |
| Postconditions    | Analyses saved and accessible                                                                                                       |
| Main Flow         | 1. User requests new analysis2. System validates authentication3. If not authenticated, prompt login4. System stores analysis state |
| Alternative Flows | Unauthenticated user → limited access                                                                                              |
| Business Rules    | Only authenticated users can persist data                                                                                           |
| Priority          | Medium                                                                                                                              |
