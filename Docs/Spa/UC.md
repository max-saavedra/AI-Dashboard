# Casos de Uso (Use Cases)

## CU-01: Carga y Procesamiento Inteligente de Datos

| Campo               | Detalle                                                                                                                                                                                                                       |
| ------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Identificador       | CU-01                                                                                                                                                                                                                         |
| Nombre              | Carga y Procesamiento Inteligente de Datos                                                                                                                                                                                    |
| Actor Principal     | Usuario                                                                                                                                                                                                                       |
| Descripción        | Permite al usuario cargar un archivo Excel/CSV con estructura no estandarizada para ser limpiado y transformado en un dataset estructurado.                                                                                   |
| Precondiciones      | Archivo válido disponible para carga                                                                                                                                                                                         |
| Postcondiciones     | Dataset limpio listo para análisis y visualización                                                                                                                                                                          |
| Flujo Principal     | 1. El usuario carga el archivo2. El sistema detecta offsets vacíos mediante heurística3. Se analiza una muestra con IA para validar tipos y nombres4. El sistema normaliza los datos5. Los datos se almacenan temporalmente |
| Flujos Alternativos | Archivo inválido → error de validaciónError de procesamiento → mensaje controlado                                                                                                                                         |
| Reglas de Negocio   | El sistema debe preservar la integridad de los datos originales                                                                                                                                                               |
| Prioridad           | Alta                                                                                                                                                                                                                          |

---

## CU-02: Generación de Dashboard y Resumen Ejecutivo

| Campo               | Detalle                                                                                                                                                               |
| ------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Identificador       | CU-02                                                                                                                                                                 |
| Nombre              | Generación de Dashboard y Resumen Ejecutivo                                                                                                                          |
| Actor Principal     | Usuario                                                                                                                                                               |
| Actores Secundarios | Servicios de IA                                                                                                                                                       |
| Descripción        | Convierte datos tabulares en visualizaciones interactivas y un resumen ejecutivo generado por IA.                                                                     |
| Precondiciones      | Datos procesados y disponibles                                                                                                                                        |
| Postcondiciones     | Dashboard renderizado y resumen generado                                                                                                                              |
| Flujo Principal     | 1. El sistema mapea columnas a tipos de gráficos2. El usuario selecciona contexto (tags)3. El sistema solicita resumen a IA4. Se renderiza el dashboard y el resumen |
| Flujos Alternativos | Timeout de IA → fallback a proveedor secundario                                                                                                                      |
| Reglas de Negocio   | Los gráficos deben seguir configuraciones predefinidas                                                                                                               |
| Prioridad           | Alta                                                                                                                                                                  |

---

## CU-03: Gestión de Historial de Análisis

| Campo               | Detalle                                                                                                                                                            |
| ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Identificador       | CU-03                                                                                                                                                              |
| Nombre              | Gestión de Historial de Análisis                                                                                                                                 |
| Actor Principal     | Usuario Registrado                                                                                                                                                 |
| Descripción        | Permite almacenar y recuperar análisis previos asociados a un usuario.                                                                                            |
| Precondiciones      | Usuario autenticado (para persistencia)                                                                                                                            |
| Postcondiciones     | Análisis guardados y accesibles                                                                                                                                   |
| Flujo Principal     | 1. El usuario solicita un nuevo análisis2. El sistema valida autenticación3. Si no está autenticado, solicita login4. El sistema guarda el estado del análisis |
| Flujos Alternativos | Usuario no autenticado → acceso limitado                                                                                                                          |
| Reglas de Negocio   | Solo usuarios autenticados pueden persistir datos                                                                                                                  |
| Prioridad           | Media                                                                                                                                                              |
