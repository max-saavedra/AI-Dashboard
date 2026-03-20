# ✅ CHECKLIST DE IMPLEMENTACIÓN

## Pre-Requisitos
- [ ] Ambiente Python 3.10+
- [ ] Supabase proyecto activo
- [ ] Variables `.env` configuradas correctamente
- [ ] Base de datos PostgreSQL activa

## 1. Actualizar Base de Datos

### ✅ Paso 1.1: Ejecutar Migración SQL
```bash
# Opción A: Supabase SQL Editor (RECOMENDADO)
1. Ve a tu proyecto Supabase
2. SQL Editor → New Query
3. Copia el contenido de: scripts/migrations/002_add_temporary_dashboards.sql
4. Click "Run" / Ejecutar

# Opción B: Via psql (si tienes acceso directo)
psql -h HOST -U USER -d DATABASE -f scripts/migrations/002_add_temporary_dashboards.sql
```

### ✅ Paso 1.2: Verificar Tabla Creada
```sql
-- En Supabase SQL Editor:
SELECT exists (
  SELECT 1 FROM information_schema.tables 
  WHERE table_name = 'temporary_dashboards'
) AS table_exists;
-- Debe retornar: true
```

## 2. Código Backend

### ✅ Paso 2.1: Verificar Imports
Los siguientes archivos ya tienen los imports correctos:
- `app/models/database.py` - ✅ TemporaryDashboard definido
- `app/api/v1/endpoints/analyze.py` - ✅ Importa TemporaryDashboard
- `app/api/v1/endpoints/auth.py` - ✅ Importa dependencias necesarias

### ✅ Paso 2.2: Reinstalar Dependencias (Si es necesario)
```bash
# Si hay cambios en requirements.txt
pip install -r requirements.txt
```

## 3. Configuración de Entorno

### ✅ Paso 3.1: Verificar .env
```bash
# Debe contener como mínimo:
DATABASE_URL=postgresql://user:password@host:port/dbname
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=xxxxx
ANON_DATA_TTL_HOURS=24
```

### ✅ Paso 3.2: Verificar .gitignore
```bash
# Debe contener:
logs/
*.log
```

## 4. Pruebas de Funcionamiento

### ✅ Test 4.1: Iniciar Servidor
```bash
# Terminal 1
cd "H:\Job\Offers\AI - Dashboard\ia-dashboard-backend"
. venv\Scripts\Activate.ps1  # Windows PowerShell

# Opción A: Desarrollo
uvicorn app.main:app --reload

# Opción B: Producción
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app
```

Debe mostrar:
- `application_starting env=development` (en logs)
- `Uvicorn running on http://127.0.0.1:8000`

### ✅ Test 4.2: Verificar Logs
```bash
# Después de iniciar servidor
ls -la logs/
# Debe existir: logs/app.log

# Contenido debe mostrar startup messages
cat logs/app.log
```

### ✅ Test 4.3: Test Endpoint Anónimo (Sin Autenticación)
```bash
# IMPORTANTE: Cambiar "testfile.xlsx" por archivo real

# Opción A: Via curl
curl -X POST "http://localhost:8000/api/v1/analyze" \
  -F "file=@test_data_dirty.csv" \
  -F "user_objective=Analizar ventas"

# Opción B: Via Python
import requests
with open('test_data_dirty.csv', 'rb') as f:
    response = requests.post(
        "http://localhost:8000/api/v1/analyze",
        files={'file': f},
        data={'user_objective': 'Analizar ventas'}
    )
    print(response.json())
```

✅ **Respuesta esperada:**
```json
{
  "dashboard_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "chat_id": null,
  "session_id": "verificar_que_existe",
  "is_temporary": true,
  "dataset_summary": "...",
  "row_count": 100,
  "columns": [...],
  "kpis": {...},
  "chart_configs": [...],
  "filter_columns": [...]
}
```

### ✅ Test 4.4: Verificar Datos en BD Temporal
```sql
-- En Supabase SQL Editor
SELECT id, session_id, expires_at, created_at
FROM temporary_dashboards
ORDER BY created_at DESC
LIMIT 1;

-- Debe haber un registro reciente
```

### ✅ Test 4.5: Test Signup y Migración
```bash
# 1. Registrarse
curl -X POST "http://localhost:8000/api/v1/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "testuser@example.com",
    "password": "Password123!"
  }'

# Guardar el access_token de la respuesta

# 2. Migrar Datos
curl -X POST "http://localhost:8000/api/v1/auth/migrate-temporary-data" \
  -H "Authorization: Bearer TOKEN_AQUI" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "session_id_anterior"
  }'
```

✅ **Respuesta esperada:**
```json
{
  "success": true,
  "message": "Successfully migrated 1 dashboard(s).",
  "migrated_count": 1
}
```

### ✅ Test 4.6: Verificar Datos Migrados
```sql
-- Datos ahora en tabla permanente
SELECT id, chat_id FROM dashboards
WHERE chat_id IN (
  SELECT id FROM chats 
  WHERE name = 'Migrated Analysis'
)
LIMIT 1;

-- La tabla temporary_dashboards debe estar vacía de ese session_id
SELECT * FROM temporary_dashboards WHERE session_id = 'xxxx';
-- Debe retornar: (0 rows)
```

## 5. Monitoreo Continuo

### ✅ Check 5.1: Revisar Logs Periódicamente
```bash
# Ver últimas líneas en tiempo real
tail -f logs/app.log

# En Windows PowerShell:
Get-Content logs/app.log -Wait
```

### ✅ Check 5.2: Monitorear Crecimiento de Logs
```bash
# Verificar tamaño
ls -lah logs/

# Si logs/app.log > 10MB, se crea backup automático
# Los 5 más recientes se mantienen
```

### ✅ Check 5.3: Limpieza de Datos Expirados
```sql
-- Ejecutar manualmente si es necesario (se auto-ejecuta después de 24h)
SELECT cleanup_expired_temporary_dashboards();

-- O verificar qué expirará
SELECT id, session_id, expires_at, NOW() as current_time,
  (expires_at - NOW()) as time_remaining
FROM temporary_dashboards
ORDER BY expires_at ASC;
```

## 6. Troubleshooting

### ❌ Problema: No se crean logs
**Solución:**
```bash
# Crear carpeta manualmente
mkdir logs

# Verificar permisos de escritura
ls -la logs/  # Debe mostrar rwx para usuario
```

### ❌ Problema: Error "table temporary_dashboards does not exist"
**Solución:**
1. Verificar migración ejecutó correctamente
2. Re-ejecutar: `scripts/migrations/002_add_temporary_dashboards.sql`
3. Esperar 10 segundos después de migración antes de reintentrar

### ❌ Problema: "prepared statement cache" errors
**Solución:**
- Ya está fijo en `app/models/session.py` con `connect_args`
- Reiniciar servidor

### ❌ Problema: Error de "module not found"
**Solución:**
```bash
# Reinstalar dependencias
pip install -r requirements.txt

# O específicamente:
pip install sqlalchemy asyncpg
```

## 7. Checklist Final

- [ ] Migración SQL ejecutada
- [ ] Tabla `temporary_dashboards` existe en BD
- [ ] Archivo `logs/` creado
- [ ] Servidor inicia sin errores
- [ ] Test endpoint anónimo funciona
- [ ] `response.is_temporary` es `true`
- [ ] `response.session_id` no es null
- [ ] Datos aparecen en `temporary_dashboards` tabla
- [ ] Test signup funciona
- [ ] Test migración funciona
- [ ] Datos migrados a tabla permanente
- [ ] Datos removidos de tabla temporal

## Documentación Adicional

- `CHANGES_SUMMARY.md` - Resumen ejecutivo de cambios
- `MIGRATION_GUIDE.md` - Guía detallada de migración
- `app/api/v1/endpoints/analyze.py` - Código del endpoint /analyze
- `app/api/v1/endpoints/auth.py` - Código del endpoint /auth/migrate-temporary-data
- `app/models/database.py` - Definición de tabla TemporaryDashboard

---

**Una vez completado este checklist, el sistema estará completamente funcional para:**
✅ Usuarios anónimos analizando archivos
✅ Logs guardándose en archivo (además de consola)
✅ Datos temporales con TTL automático
✅ Migración de datos al registrarse
