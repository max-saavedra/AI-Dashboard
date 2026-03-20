# RF-01: Ingesta y Normalización de Archivos (ETL Local)

| Campo                    | Detalle                                                                                                                                                                                        |
| ------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Identificador            | RF-01                                                                                                                                                                                          |
| Nombre                   | Carga y Limpieza Inteligente de Datasets                                                                                                                                                       |
| Descripción             | El sistema debe permitir la carga de archivos .xlsx y .csv, eliminando offsets vacíos, gestionando celdas unidas y normalizando encabezados para generar una estructura tabular consistente.  |
| Actores                  | Usuario Final, Backend System                                                                                                                                                                  |
| Prioridad                | Crítica                                                                                                                                                                                       |
| Precondiciones           | Archivo no corrupto; tamaño ≤ 10 MB; formatos permitidos (.xlsx, .csv)                                                                                                                       |
| Postcondiciones          | Dataset limpio como DataFrame; datos disponibles en memoria o persistidos                                                                                                                      |
| Flujo Básico            | 1. Carga de archivo<br />2. Detección de primera celda no nula<br />3. Eliminación de offsets vacíos<br />4. Procesamiento de celdas unidas<br />5. Normalización de columnas (snake_case) |
| Excepciones              | Archivo vacío (error 422); formato no soportado (error 422); error de lectura                                                                                                                 |
| Reglas de Negocio        | Resolver celdas unidas usando celda principal; debe existir al menos una tabla válida                                                                                                         |
| Criterios de Aceptación | JSON estructurado con datos limpios; sin columnas vacías; consistencia de datos                                                                                                               |
| Dependencias             | pandas, openpyxl                                                                                                                                                                               |
| Supuestos                | Existe al menos una tabla interpretable                                                                                                                                                        |

---

# RF-02: Análisis de Estructura y Tipado de Datos

| Campo                    | Detalle                                                                                                                        |
| ------------------------ | ------------------------------------------------------------------------------------------------------------------------------ |
| Identificador            | RF-02                                                                                                                          |
| Nombre                   | Detección de Schema mediante IA                                                                                               |
| Descripción             | El sistema analiza el dataset mediante heurísticas y modelos de IA para identificar tipos de datos y sugerir visualizaciones. |
| Actores                  | Backend System, Servicio de IA                                                                                                 |
| Prioridad                | Alta                                                                                                                           |
| Precondiciones           | RF-01 completado                                                                                                               |
| Postcondiciones          | Metadatos generados; sugerencias de visualización disponibles                                                                 |
| Flujo Básico            | 1. Profiling de datos<br />2. Extracción de muestra<br />3. Envío a IA<br />4. Recepción de JSON con tipos y gráficos      |
| Excepciones              | Falla de API → heurísticas locales; timeout → fallback                                                                      |
| Reglas de Negocio        | No enviar datos sensibles; anonimización si aplica; IA complementa análisis                                                  |
| Criterios de Aceptación | ≥95% columnas correctamente tipadas; mínimo 3 gráficos sugeridos                                                            |
| Dependencias             | API Gemini / OpenAI                                                                                                            |

---

# RF-03: Generación de Resumen Ejecutivo

| Campo                    | Detalle                                                                                                                 |
| ------------------------ | ----------------------------------------------------------------------------------------------------------------------- |
| Identificador            | RF-03                                                                                                                   |
| Nombre                   | Generación de Resumen Ejecutivo con IA                                                                                 |
| Descripción             | Generación de resumen en lenguaje natural basado en datos procesados e insights, con fallback entre proveedores de IA. |
| Actores                  | Usuario Final, Servicios de IA                                                                                          |
| Prioridad                | Alta                                                                                                                    |
| Precondiciones           | Datos procesados; insights generados                                                                                    |
| Postcondiciones          | Resumen disponible para visualización y descarga                                                                       |
| Flujo Básico            | 1. Construcción de contexto<br />2. Llamada a IA<br />3. Fallback si hay latencia<br />4. Renderizado del resumen      |
| Excepciones              | Timeout → fallback; error → mensaje controlado                                                                        |
| Reglas de Negocio        | El resumen debe reflejar datos reales; exportable a PDF                                                                 |
| Criterios de Aceptación | Insights coherentes; sin contradicciones con datos                                                                      |
| Dependencias             | Gemini SDK, OpenAI SDK, ReportLab                                                                                       |

---

# RF-04: Gestión de Sesiones y Persistencia

| Campo                    | Detalle                                                                                                          |
| ------------------------ | ---------------------------------------------------------------------------------------------------------------- |
| Identificador            | RF-04                                                                                                            |
| Nombre                   | Gestión de Historial y Registro Condicional                                                                     |
| Descripción             | Permite múltiples sesiones de análisis con persistencia condicionada a registro de usuario.                    |
| Actores                  | Usuario Final                                                                                                    |
| Prioridad                | Media                                                                                                            |
| Precondiciones           | Ninguna                                                                                                          |
| Postcondiciones          | Chats persistidos y asociados al usuario                                                                         |
| Flujo Básico            | 1. Inicio anónimo<br />2. Intento de nuevo análisis<br />3. Solicitud de login<br />4. Asociación de sesiones |
| Excepciones              | Usuario no se registra → no persistencia; cierre → limpieza                                                    |
| Reglas de Negocio        | Usuario anónimo solo 1 sesión; persistencia requiere autenticación                                            |
| Criterios de Aceptación | Recuperación de análisis previos; no recarga de archivos                                                       |
| Dependencias             | Supabase Auth, JWT                                                                                               |

---

# RF-05: Visualización y Dashboard Interactivo

| Campo                    | Detalle                                                                                                                             |
| ------------------------ | ----------------------------------------------------------------------------------------------------------------------------------- |
| Identificador            | RF-05                                                                                                                               |
| Nombre                   | Dashboard Dinámico con Filtros                                                                                                     |
| Descripción             | Generación de dashboard interactivo con gráficos dinámicos y filtros aplicables sobre los datos.                                 |
| Actores                  | Usuario Final                                                                                                                       |
| Prioridad                | Alta                                                                                                                                |
| Precondiciones           | Datos procesados                                                                                                                    |
| Postcondiciones          | Dashboard renderizado                                                                                                               |
| Flujo Básico            | 1. Generación de gráficos<br />2. Configuración por usuario<br />3. Aplicación de filtros<br />4. Actualización en tiempo real |
| Excepciones              | Dataset grande → sampling o agregación                                                                                            |
| Reglas de Negocio        | Uso de gráficos predefinidos; filtros generados automáticamente                                                                   |
| Criterios de Aceptación | Tiempo de respuesta < 200 ms; consistencia visual                                                                                   |
| Dependencias             | VueJS, Chart.js, ApexCharts                                                                                                         |

---

# RF-06: Asistente de Consultas sobre Datos (Q&A)

| Campo                    | Detalle                                                                                                                 |
| ------------------------ | ----------------------------------------------------------------------------------------------------------------------- |
| Identificador            | RF-06                                                                                                                   |
| Nombre                   | Chat de Consultas sobre Dataset                                                                                         |
| Descripción             | Permite consultas en lenguaje natural sobre el dataset, con respuestas basadas exclusivamente en los datos disponibles. |
| Actores                  | Usuario Final, Servicio de IA                                                                                           |
| Prioridad                | Media                                                                                                                   |
| Precondiciones           | Dataset cargado                                                                                                         |
| Postcondiciones          | Respuesta generada                                                                                                      |
| Flujo Básico            | 1. Usuario consulta<br />2. Construcción de contexto<br />3. Llamada a IA<br />4. Respuesta                            |
| Excepciones              | Pregunta ambigua → aclaración; error IA → fallback                                                                   |
| Reglas de Negocio        | Respuestas basadas solo en datos; no inferencias externas                                                               |
| Criterios de Aceptación | Respuestas coherentes; sin alucinaciones                                                                                |
| Dependencias             | API LLM (Gemini / OpenAI)                                                                                               |
