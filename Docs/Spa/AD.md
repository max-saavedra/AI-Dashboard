# Arquitectura de Datos – IA Dashboard

## 1. Flujo de Datos (Data Pipeline)

El ciclo de vida de los datos se estructura en cuatro etapas clave:

1. **Ingestión**
2. **Procesamiento y Normalización**
3. **Enriquecimiento (IA)**
4. **Persistencia y Consumo**

Este pipeline garantiza la transformación continua desde datos crudos hasta insights accionables.

---

## 2. Capas de la Arquitectura de Datos

### 2.1 Capa de Ingestión (Raw Layer)

**Origen:**

- Archivos binarios (`.xlsx`, `.csv`) cargados mediante `multipart/form-data`

**Estrategia de Procesamiento:**

- Los archivos se cargan en memoria en el backend (FastAPI) utilizando `BytesIO`
- Para escenarios productivos:
  - Se recomienda subir archivos a **Google Cloud Storage**
  - Procesarlos de forma asíncrona

**Características:**

- Manejo de datos efímeros
- Validación y sanitización de entrada
- Mínima transformación inicial

---

### 2.2 Capa de Procesamiento y Normalización (Silver Layer)

Esta capa transforma los datos crudos en un formato estructurado y analizable.

#### Detección de Offset

- Se aplica una **heurística de densidad de datos**
- Si las primeras *N* filas contienen más del 80% de valores nulos:
  - Se descartan
  - Se identifica la cabecera real

#### Normalización de Schema

- Se utiliza un **Schema Agent (Gemini 1.5 Flash)**
- Se analiza una muestra del dataset
- La IA devuelve metadatos estructurados:

Ejemplo:

- Columna: `Vta_2024` → Tipo: `Float`, Alias: `Ventas 2024`

#### Manejo de Celdas Unidas

- Implementado con **Forward Fill (`ffill`) de Pandas**
- Garantiza que cada fila tenga contexto completo

#### Salida

- DataFrame limpio y normalizado
- Nombres de columnas consistentes (snake_case)
- Dataset tipado listo para análisis

---

### 2.3 Capa de Enriquecimiento e Insights (Gold Layer)

Esta capa transforma los datos estructurados en conocimiento de negocio.

#### Agregaciones Dinámicas

- Cálculo de KPIs:
  - Promedios
  - Máximos y mínimos
  - Tendencias temporales

#### Contextualización con IA

- No se envía el dataset completo al LLM
- Se envía únicamente:
  - Métricas agregadas
  - Tags seleccionados por el usuario
  - Resumen estructurado

#### Beneficios

- Reducción de uso de tokens
- Menor costo operativo
- Mayor velocidad de respuesta
- Control determinístico del análisis

#### Salida

- Resumen ejecutivo
- Insights clave
- Metadatos analíticos estructurados

---

## 3. Modelo de Datos (Diseño de Base de Datos)

El sistema utiliza **PostgreSQL (Supabase)**, combinando un modelo relacional con el uso de **JSONB** para flexibilidad.

---

### Tabla: `users` (Gestionada por Supabase Auth)

| Columna | Tipo      | Descripción                     |
| ------- | --------- | -------------------------------- |
| id      | UUID (PK) | Identificador único del usuario |
| email   | String    | Correo electrónico              |

---

### Tabla: `chats` (Hilos de Análisis)

| Columna    | Tipo      | Descripción                                    |
| ---------- | --------- | ----------------------------------------------- |
| id         | UUID (PK) | Identificador del chat                          |
| user_id    | UUID (FK) | Relación con usuario (nullable para anónimos) |
| name       | String    | Nombre del chat (ej. "Ventas Marzo")            |
| created_at | Timestamp | Fecha de creación                              |

---

### Tabla: `dashboards` (Entidad Principal)

| Columna      | Tipo      | Descripción                        |
| ------------ | --------- | ----------------------------------- |
| id           | UUID (PK) | Identificador único                |
| chat_id      | UUID (FK) | Relación con chat                  |
| cleaned_data | JSONB     | Dataset limpio en formato JSON      |
| ai_insights  | JSONB     | Insights y resumen generados por IA |
| chart_config | JSONB     | Configuración de visualizaciones   |
| metadata     | JSONB     | Metadatos: archivo, tags, schema    |

---

## 4. Estrategia de Persistencia y Ciclo de Vida

### 4.1 Manejo de Datos Anónimos

- Se almacenan con `user_id = NULL`
- Eliminación automática mediante tarea programada:

```sql
DELETE FROM dashboards
WHERE user_id IS NULL
AND created_at < NOW() - INTERVAL '24 hours';
```

---

### 4.2 Seguridad de Datos

* Implementación de **Row Level Security (RLS)** en Supabase
* Garantiza:
  * Aislamiento total entre usuarios
  * Acceso únicamente a datos propios

**Alineación:**

* Buenas prácticas de privacidad
* Estándares éticos (enfoque BCorp)

---

### 4.3 Estrategia de Performance

* Los datos procesados se envían una sola vez al frontend
* Los filtros se ejecutan completamente en cliente:
  * Filtrado reactivo en VueJS
  * Sin llamadas adicionales al backend

**Beneficios:**

* Baja latencia
* Mejor experiencia de usuario
* Reducción de carga en backend

---

## 5. Backlog Inicial del ETL (Backend)

### Task 1: Ingesta de Archivos

* Configurar FastAPI con `python-multipart`
* Implementar endpoint de carga

---

### Task 2: Servicio de Limpieza

* Crear servicio `ExcelCleaner` con Pandas
* Eliminar filas vacías con `dropna`
* Detectar inicio de tabla dinámicamente

---

### Task 3: Detección de Schema con IA

* Diseñar prompt para Gemini
* Input: `df.head()`
* Output:
  * Tipos de datos
  * Alias
  * Roles sugeridos

---

### Task 4: Endpoint de Análisis

* Implementar `POST /analyze`
* Orquestar:
  * Ingestión
  * Limpieza
  * Tipado
  * Enriquecimiento IA

---

## 6. Conclusión

Esta arquitectura de datos permite:

* Transformar datos no estructurados en insights accionables
* Utilizar IA de forma eficiente y controlada
* Almacenar datos de forma flexible con JSONB
* Garantizar alto rendimiento con baja latencia

Además, establece una base sólida para evolucionar hacia:

* Pipelines de datos avanzados
* Procesamiento en tiempo real
* Sistemas de decisión basados en IA
