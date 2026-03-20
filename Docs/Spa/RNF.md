# RNF-01: Latencia de Procesamiento

| Campo                    | Detalle                                                                                                                              |
| ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------ |
| Identificador            | RNF-01                                                                                                                               |
| Nombre                   | Latencia de Procesamiento                                                                                                            |
| Descripción             | El sistema debe procesar y limpiar archivos de manera eficiente para garantizar una experiencia fluida.                              |
| Categoría               | Performance                                                                                                                          |
| Requerimiento            | El sistema debe procesar y limpiar archivos de hasta 5 MB en menos de 3 segundos, excluyendo el tiempo de respuesta de la API de IA. |
| Métrica                 | Tiempo de procesamiento (segundos)                                                                                                   |
| Criterios de Aceptación | Archivos ≤ 5 MB procesados en < 3 segundos bajo condiciones normales                                                                |
| Dependencias             | pandas, motor de procesamiento backend                                                                                               |

---

# RNF-02: Tiempo de Respuesta de la Interfaz

| Campo                    | Detalle                                                                                               |
| ------------------------ | ----------------------------------------------------------------------------------------------------- |
| Identificador            | RNF-02                                                                                                |
| Nombre                   | Tiempo de Respuesta del Frontend                                                                      |
| Descripción             | El sistema debe garantizar respuestas rápidas ante interacciones del usuario.                        |
| Categoría               | Performance                                                                                           |
| Requerimiento            | Las visualizaciones y filtros deben actualizarse en menos de 200 ms tras la interacción del usuario. |
| Métrica                 | Latencia de UI (milisegundos)                                                                         |
| Criterios de Aceptación | Todas las interacciones actualizan gráficos en < 200 ms                                              |
| Dependencias             | VueJS, procesamiento en cliente                                                                       |

---

# RNF-03: Manejo de Concurrencia

| Campo                    | Detalle                                                                                                                        |
| ------------------------ | ------------------------------------------------------------------------------------------------------------------------------ |
| Identificador            | RNF-03                                                                                                                         |
| Nombre                   | Manejo de Solicitudes Concurrentes                                                                                             |
| Descripción             | El backend debe soportar múltiples usuarios simultáneos sin degradación.                                                    |
| Categoría               | Performance                                                                                                                    |
| Requerimiento            | El sistema debe manejar al menos 50 solicitudes concurrentes de procesamiento de archivos utilizando programación asíncrona. |
| Métrica                 | Número de solicitudes concurrentes                                                                                            |
| Criterios de Aceptación | ≥ 50 solicitudes concurrentes sin fallos                                                                                      |
| Dependencias             | FastAPI, async/await                                                                                                           |

---

# RNF-04: Estrategia de Fallback de IA

| Campo                    | Detalle                                                                    |
| ------------------------ | -------------------------------------------------------------------------- |
| Identificador            | RNF-04                                                                     |
| Nombre                   | Resiliencia y Fallback de IA                                               |
| Descripción             | El sistema debe garantizar continuidad ante fallos de APIs externas de IA. |
| Categoría               | Reliability                                                                |
| Requerimiento            | Implementar timeout y fallback entre proveedores de IA.                    |
| Métrica                 | Tiempo de conmutación                                                     |
| Criterios de Aceptación | Si la IA primaria supera 8 segundos, se activa fallback automáticamente   |
| Dependencias             | API Gemini, API OpenAI                                                     |

---

# RNF-05: Persistencia Volátil

| Campo                    | Detalle                                                                          |
| ------------------------ | -------------------------------------------------------------------------------- |
| Identificador            | RNF-05                                                                           |
| Nombre                   | Persistencia Temporal de Datos                                                   |
| Descripción             | El sistema debe gestionar datos temporales de usuarios no registrados.           |
| Categoría               | Reliability                                                                      |
| Requerimiento            | Los datos deben persistir solo durante la sesión y eliminarse tras inactividad. |
| Métrica                 | Tiempo de retención                                                             |
| Criterios de Aceptación | Eliminación automática tras 30 minutos de inactividad                          |
| Dependencias             | Gestión de sesiones backend                                                     |

---

# RNF-06: Seguridad de API Keys

| Campo                    | Detalle                                                                       |
| ------------------------ | ----------------------------------------------------------------------------- |
| Identificador            | RNF-06                                                                        |
| Nombre                   | Protección de Claves API                                                     |
| Descripción             | Las credenciales sensibles deben manejarse de forma segura.                   |
| Categoría               | Security                                                                      |
| Requerimiento            | Las claves API no deben exponerse en el frontend.                             |
| Métrica                 | Incidentes de exposición                                                     |
| Criterios de Aceptación | Todas las llamadas a IA se realizan desde backend usando variables de entorno |
| Dependencias             | Variables de entorno, arquitectura backend                                    |

---

# RNF-07: Sanitización de Datos

| Campo                    | Detalle                                                                             |
| ------------------------ | ----------------------------------------------------------------------------------- |
| Identificador            | RNF-07                                                                              |
| Nombre                   | Validación de Archivos de Entrada                                                  |
| Descripción             | El sistema debe prevenir la ejecución de contenido malicioso en archivos cargados. |
| Categoría               | Security                                                                            |
| Requerimiento            | Validar y sanitizar archivos antes de su procesamiento.                             |
| Métrica                 | Cobertura de validación                                                            |
| Criterios de Aceptación | No se ejecutan scripts ni fórmulas maliciosas                                      |
| Dependencias             | Lógica de validación, pandas                                                      |

---

# RNF-08: Autenticación Condicional

| Campo                    | Detalle                                                        |
| ------------------------ | -------------------------------------------------------------- |
| Identificador            | RNF-08                                                         |
| Nombre                   | Control de Acceso Seguro                                       |
| Descripción             | El acceso a datos persistidos debe estar restringido.          |
| Categoría               | Security                                                       |
| Requerimiento            | Solo usuarios autenticados pueden acceder a datos almacenados. |
| Métrica                 | Validación de accesos                                         |
| Criterios de Aceptación | Usuarios solo acceden a sus propios datos                      |
| Dependencias             | Supabase Auth, JWT                                             |

---

# RNF-09: Arquitectura Stateless

| Campo                    | Detalle                                                    |
| ------------------------ | ---------------------------------------------------------- |
| Identificador            | RNF-09                                                     |
| Nombre                   | Backend sin Estado                                         |
| Descripción             | El backend debe permitir escalabilidad horizontal.         |
| Categoría               | Maintainability                                            |
| Requerimiento            | El sistema no debe almacenar estado de sesión localmente. |
| Métrica                 | Cumplimiento stateless                                     |
| Criterios de Aceptación | Escalabilidad horizontal sin conflictos de sesión         |
| Dependencias             | Docker, infraestructura cloud                              |

---

# RNF-10: Observabilidad

| Campo                    | Detalle                                                     |
| ------------------------ | ----------------------------------------------------------- |
| Identificador            | RNF-10                                                      |
| Nombre                   | Logging y Monitoreo                                         |
| Descripción             | El sistema debe permitir trazabilidad de eventos críticos. |
| Categoría               | Maintainability                                             |
| Requerimiento            | Registrar eventos clave y errores del sistema.              |
| Métrica                 | Cobertura de logs                                           |
| Criterios de Aceptación | Logs incluyen procesamiento, latencia de IA y errores       |
| Dependencias             | Framework de logging                                        |

---

# RNF-11: Compatibilidad Multiplataforma

| Campo                    | Detalle                                                                         |
| ------------------------ | ------------------------------------------------------------------------------- |
| Identificador            | RNF-11                                                                          |
| Nombre                   | Soporte Multiplataforma                                                         |
| Descripción             | El sistema debe ejecutarse en distintos sistemas operativos sin modificaciones. |
| Categoría               | Usability / DevOps                                                              |
| Requerimiento            | El proyecto debe correr en Windows, Linux y macOS.                              |
| Métrica                 | Compatibilidad de entorno                                                       |
| Criterios de Aceptación | Uso de requirements.txt y package.json estándar                                |
| Dependencias             | Python, Node.js                                                                 |

---

# RNF-12: Integración Continua

| Campo                    | Detalle                                                      |
| ------------------------ | ------------------------------------------------------------ |
| Identificador            | RNF-12                                                       |
| Nombre                   | Pipeline CI/CD                                               |
| Descripción             | El sistema debe garantizar calidad mediante automatización. |
| Categoría               | DevOps                                                       |
| Requerimiento            | Implementar CI con pruebas automáticas antes de despliegue. |
| Métrica                 | Tasa de éxito del pipeline                                  |
| Criterios de Aceptación | Tests ejecutados automáticamente antes de despliegue        |
| Dependencias             | GitHub Actions, plataforma de despliegue                     |

---

# Resumen de Atributos de Calidad

| Atributo     | Objetivo                                | Herramienta Clave                     |
| ------------ | --------------------------------------- | ------------------------------------- |
| Portabilidad | Ejecutar en cualquier sistema operativo | Docker / entornos virtuales           |
| Robustez     | Evitar fallos ante errores de IA        | Lógica de fallback                   |
| Privacidad   | Protección de datos de usuario         | JWT / limpieza de sesiones            |
| Performance  | Alta velocidad en procesamiento y UI    | Cliente optimizado, backend eficiente |
