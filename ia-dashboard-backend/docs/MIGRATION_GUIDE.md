# Instrucciones de Migración - Tabla Temporal de Dashboards

## Resumen de cambios

Se han añadido las siguientes mejoras:

### 1. **Soporte para dashboards anónimos (sin autenticación)**
   - Nuevos usuarios pueden crear dashboards sin registrarse
   - Los datos se guardan en la tabla `temporary_dashboards` con TTL de 24 horas
   - Cada sesión anónima obtiene un `session_id` único
   - Cuando los datos expiran, se eliminan automáticamente

### 2. **Logging mejorado**
   - Los logs se guardan tanto en consola como en archivo (`logs/app.log`)
   - Rotación de archivos: máximo 10 MB, mantiene 5 copias(
   - Ayuda a diagnosticar problemas sin perder historial

### 3. **Migración de datos temporales**
   - Nuevo endpoint: `POST /api/v1/auth/migrate-temporary-data`
   - Permite que usuarios autenticados recuperen sus análisis anónimos previos
   - Usa el `session_id` devuelto en la respuesta del `/analyze`

## Pasos para aplicar los cambios

### Paso 1: Ejecutar la migración SQL

Accede a tu Supabase SQL Editor y ejecuta el contenido del archivo:
```
scripts/migrations/002_add_temporary_dashboards.sql
```

Esto creará:
- Tabla `temporary_dashboards` con campos de metadata
- Índices para performance en `session_id` y `expires_at`
- Función `cleanup_expired_temporary_dashboards()` para limpieza manual

### Paso 2: (Opcional) Configurar limpieza automática

Si tu versión de Supabase soporta `pg_cron`, ejecuta:
```sql
SELECT cron.schedule('cleanup_temp_dashboards', '0 * * * *', 'SELECT cleanup_expired_temporary_dashboards();');
```

Esto ejecutará limpieza cada hora.

### Paso 3: Reiniciar la aplicación

```bash
# En desarrollo
uvicorn app.main:app --reload

# En producción
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app
```

## Flujo de usuario

### Usuario anónimo:
1. Sube un archivo Excel a `POST /api/v1/analyze`
2. Recibe respuesta con:
   - `is_temporary: true`
   - `session_id: "..."` (guarda este valor)
   - `dashboard_id: "..."` y datos del análisis

### Usuario se registra:
1. Completa registro en `POST /api/v1/auth/signup`
2. (Opcional) Migra análisis previos:
   ```json
   POST /api/v1/auth/migrate-temporary-data
   {
     "session_id": "valor_recibido_anteriormente"
   }
   ```
3. Los dashboards anónimos se convierten en permanentes y se guardan en Supabase

## Notas importantes

- Los logs se guardan en la carpeta `logs/` - **no committear** (actualizacio en `.gitignore`)
- El TTL de datos temporales se configura en `.env` con `ANON_DATA_TTL_HOURS` (default: 24h)
- Los datos temporales no se persisten después de reimiciar si no se llama a la migración
- Los datos que expiren serán eliminados automáticamente

## Variables de entorno requeridas

```bash
# .env
ANON_DATA_TTL_HOURS=24  # Horas antes de que expiren datos temporales
DATABASE_URL=postgresql://...  # URL de Supabase con credenciales correctas
```

## Troubleshooting

Si los logs no aparecen:
- Verifica que la carpeta `logs/` existe o se crea automáticamente
- Revisa permisos de escritura en el directorio del proyecto
- En Windows, asegúrate de usar rutas correctas (se crean automáticamente)

Si la migración no funciona:
- Verifica que `temporary_dashboards` existe: `SELECT * FROM information_schema.tables WHERE table_name='temporary_dashboards';`
- Comprueba que no hay conflictos de session_id duplicados
- Revisa los logs para mensajes de error específicos
