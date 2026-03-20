# Resumen de Cambios - Solución de Problemas de Peticiones y Almacenamiento

## Problemas Resueltos

✅ **1. Peticiones sin respuesta / Sin logs**
- Configuré logging a archivo (`logs/app.log`) además de consola
- Los logs ahora se guardan con rotación (10 MB máximo, 5 backups)
- Disablité caché de prepared statements en asyncpg para compatibilidad con PgBouncer/Supabase

✅ **2. Dashboards sin autenticación que se pierden al reiniciar**
- Creé tabla `temporary_dashboards` con TTL automático de 24 horas
- Los usuarios anónimos ahora pueden crear dashboards que se guardan localmente
- Cada sesión anónima recibe un `session_id` único

✅ **3. Sincronización de datos al registrarse**
- Nuevo endpoint `/api/v1/auth/migrate-temporary-data` 
- Cuando un usuario se registra, puede recuperar todos sus análisis anónimos previos
- Los datos se migran de la tabla temporal a la permanente

## Archivos Modificados

### Backend - Núcleo
| Archivo | Cambio | Motivo |
|---------|--------|--------|
| `app/models/database.py` | ➕ Tabla `TemporaryDashboard` | Almacenar análisis anónimos |
| `app/models/session.py` | ➕ `connect_args` sin caché | Compatibilidad PgBouncer |
| `app/core/logging.py` | ➕ Rotación de logs a archivo | Debug y análisis histórico |

### API Endpoints
| Archivo | Cambio | Motivo |
|---------|--------|--------|
| `app/api/v1/endpoints/analyze.py` | 🔄 Guardar anónimo en temporal | Soportar usuarios sin auth |
| `app/api/v1/endpoints/auth.py` | ➕ POST `/auth/migrate-temporary-data` | Recuperar datos anónimos |
| `app/schemas/analysis.py` | ➕ Campos `is_temporary`, `session_id` | Indicar tipo de almacenamiento |

### Base de Datos & Configuración
| Archivo | Cambio | Motivo |
|---------|--------|--------|
| `scripts/migrations/002_add_temporary_dashboards.sql` | ➕ Nueva migración SQL | Crear tabla temporal con TTL |
| `.gitignore` | ➕ `logs/` y `*.log` | No commitear archivos de log |
| `MIGRATION_GUIDE.md` | ➕ Documentación completa | Guía de implementación |

## Flujo Actual de Usuario

### 1️⃣ Usuario Anónimo Analiza Excel
```
POST /api/v1/analyze (sin token)
│
├─ Procesa archivo
├─ Guarda en: temporary_dashboards (24h TTL)
└─ Retorna: { is_temporary: true, session_id: "...", dashboard_id: "..." }
```
Frontend debe guardar `session_id` en localStorage/sessionStorage

### 2️⃣ Usuario se Registra
```
POST /api/v1/auth/signup
│
├─ Crea cuenta en Supabase Auth
├─ Crea registro en tabla users
└─ Devuelve: { access_token, user_id, ... }
```

### 3️⃣ (Opcional) Usuario Recupera Datos Anónimos
```
POST /api/v1/auth/migrate-temporary-data
{
  "session_id": "valor_guardado_en_paso_1"
}
│
├─ Verifica autenticación
├─ Busca dashboards en temporary_dashboards
├─ Mueve a dashboards (permanente)
└─ Borra de temporary_dashboards
```
Retorna: `{ success: true, migrated_count: N }`

## Cómo Implementar

### 1. Ejecutar Migración SQL (Una sola vez)
```bash
# En Supabase SQL Editor, copiar y ejecutar:
# scripts/migrations/002_add_temporary_dashboards.sql
```

### 2. Reiniciar Backend
```bash
uvicorn app.main:app --reload
```

### 3. Frontend debe:
- Capturar `session_id` de respuesta `/analyze`
- Guardarlo en `sessionStorage` o enviar a backend
- Después de registrarse, llamar a `/auth/migrate-temporary-data` si hay `session_id`

## Validación de Cambios

### Verificar logs creándose:
```bash
# Debería existir después de primera petición
ls -la logs/app.log
```

### Verificar tabla temporal:
```sql
SELECT * FROM temporary_dashboards LIMIT 1;
-- Debería mostrar estructura con: id, session_id, cleaned_data, expires_at
```

### Probar endpoint anónimo:
```bash
curl -X POST "http://localhost:8000/api/v1/analyze" \
  -F "file=@testfile.xlsx"
# Debe retornar JSON con is_temporary: true, session_id: "..."
```

### Probar migración:
```bash
# 1. Obtener token de signup
# 2. Llamar con token y session_id previo
curl -X POST "http://localhost:8000/api/v1/auth/migrate-temporary-data" \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"session_id": "valor_anterior"}'
```

## Características Nuevas

✨ **Logging Robusto**
- Consola: Salida legible en desarrollo
- Archivo: JSON estructurado para parse
- Rotación automática (10MB límite)

✨ **Persistencia Flexible**
- Datos temporales: 24h por defecto (configurable)
- Limpieza automática de expirados
- Sin perder datos - migración explícita antes de expirar

✨ **Sin Dependencias Nuevas**
- Solo cambios en código existente
- Usa SQLAlchemy que ya está presente
- Logging con structlog que ya está en uso

## Notas Importantes

⚠️ **Data TTL**
- Default: 24 horas (configurable en `.env` con `ANON_DATA_TTL_HOURS`)
- Las funciones de API son stateless
- Limpieza automática con función SQL

⚠️ **Session ID**
- Generado con `secrets.token_urlsafe(32)` - criptográficamente seguro
- Único por sesión anónima
- Frontend debe guardarlo para migración posterior

⚠️ **Sin cambios requeridos en Frontend**
Como mínimo:
1. Recibir `session_id` y `is_temporary` de `/analyze`
2. Mostrar indicador si es temporal
3. Sugerir migración post-signup

## Próximos Pasos Opcionales

1. **Limpiezaautomática periódica** con pg_cron (SQL en migración)
2. **Notificación al usuario** cuando datos van a expirar
3. **Compartir datos anónimos** con unique link antes de expirar
4. **Dashboard para ver historial** de análisis temporales

---

**Todos los cambios mantienen la lógica del proyecto sin archivos redundantes.**
