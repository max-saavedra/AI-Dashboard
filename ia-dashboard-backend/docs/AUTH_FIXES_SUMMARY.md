# 🔧 Auth.py Fixes & Timeout Resolution

## Cambios Realizados

### 1. **app/api/v1/endpoints/auth.py**

#### Antes ❌
- Manejo genérico de excepciones
- Sin logging detallado de errores de Supabase
- Timeouts muy cortos (no daba tiempo a Supabase responder)
- Mensaje de error vago: "Failed to create account"

#### Después ✅
- Detección específica de errores:
  - `email_already_registered` → 409 Conflict
  - `weak_password` → 400 Bad Request
  - `timeout` → 504 Gateway Timeout
  - `invalid_credentials` → 401 Unauthorized
- Logging detallado en cada paso
- Mejor configuración del cliente Supabase
- Mensajes de error específicos y útiles
- Mejor manejo de respuestas de Supabase

#### Código Nuevo

```python
# Inicialización mejorada:
supabase: Client = create_client(
    settings.supabase_url,
    settings.supabase_anon_key,
    options={"http2": False}  # Para compatibilidad
)

# Función para extraer errores específicos:
def _extract_error_message(exc: Exception) -> tuple[str, int]:
    error_str = str(exc).lower()
    
    if "user already exists" in error_str:
        return "email_already_registered", status.HTTP_409_CONFLICT
    
    if "timeout" in error_str:
        return "timeout", status.HTTP_504_GATEWAY_TIMEOUT
    
    # ... más detecciones
```

### 2. **scripts/test_auth.py**

#### Mejoras
- ✓ Timeout aumentado a 30 segundos (antes 10)
- ✓ Mejor manejo de tiempo límite
- ✓ Mensajes de error más detallados
- ✓ Test de login agregado
- ✓ Mejor reporting de resultados

```python
# Antes:
async with httpx.AsyncClient() as client:
    response = await client.post(..., timeout=10.0)

# Ahora:
async with httpx.AsyncClient(timeout=30.0) as client:
    response = await client.post(...)
    # Manejo específico de timeouts
```

### 3. **Documentación Nueva**

Creé: `docs/SUPABASE_TROUBLESHOOTING.md`
- Guía completa de debugging
- Checklist de configuración
- Problemas específicos y soluciones
- Testing step-by-step

---

## Qué Puede Estar Causando el Timeout

### 1. Email ya registrado en Supabase
```
Status 400: "Email already registered"
```
**Solución:** Usa email con timestamp:
```python
import time
email = f"test{int(time.time())}@example.com"  # test1773953130806@example.com
```

### 2. Credenciales Supabase Incorrectas
```
Timeout después de 60 segundos
```
**Verificar en .env:**
```
SUPABASE_URL=https://yrenqasaehjoxzzoxqgr.supabase.co  ✓
SUPABASE_ANON_KEY=eyJhbGciOi...  ✓ (debe empezar con eyJ)
```

### 3. Problema de Conexión a Supabase
```
NetworkError after X segundos
```
**Verificar:**
```bash
# ¿Puedes alcanzar Supabase?
ping yrenqasaehjoxzzoxqgr.supabase.co
curl -I https://yrenqasaehjoxzzoxqgr.supabase.co
```

### 4. JWKS Cache Problem
Viste que en `security.py` se cambió a ES256 con JWKS. Si hay error:
```
DEBUG: JWT validation failed - JWKS fetch error
```
**Solución:**
```python
# En security.py, line 8:
JWKS_URL = f"{settings.supabase_url}/auth/v1/.well-known/jwks.json"
# Debe ser accesible online
```

---

## Cómo Probar Ahora

### Opción 1: Script automatizado (recomendado)
```bash
python scripts/test_auth.py
```

Esto te mostrará:
- ✓ Si puedes conectarte a Supabase
- ✓ Si signup funciona
- ✓ Si login funciona
- ✓ Si tokens son válidos

### Opción 2: Manual con curl
```bash
# 1. Signup
curl -X POST http://localhost:8000/api/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"test'$(date +%s)'@example.com","password":"TestPassword123!"}'

# 2. Copiar access_token de respuesta e intentar:
TOKEN="eyJhbGc..."
curl -X GET http://localhost:8000/api/v1/chats \
  -H "Authorization: Bearer $TOKEN"
```

### Opción 3: Desde el frontend
```javascript
// En browser console:
const response = await fetch('http://localhost:8000/api/v1/auth/signup', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: `test${Date.now()}@example.com`,
    password: 'TestPassword123!'
  })
});
const data = await response.json();
console.log('Status:', response.status);
console.log('Data:', data);
```

---

## Logs Esperados

### ✓ Signup exitoso (30 segundos)
```
DEBUG: Signup attempt started email=test1773953130806@example.com
DEBUG: Calling Supabase sign_up email=test1773953130806@example.com
DEBUG: Supabase sign_up response received has_user=True has_session=True
DEBUG: Signup and auto-signin successful user_id=... email=...
Status: 201
```

### ✗ Email ya registrado (rápido, <1 segundo)
```
DEBUG: Signup attempt started email=test@example.com
DEBUG: Calling Supabase sign_up
DEBUG: Extracting error info exception_type=... 
DEBUG: Email already registered error detected
Status: 409
Detail: "This email is already registered"
```

### ✗ Timeout (>60 segundos, luego error)
```
DEBUG: Signup attempt started email=test@example.com
DEBUG: Calling Supabase sign_up
[... espera 60+ segundos ...]
TimeoutError: Request timeout - Supabase server not responding
```

---

## Cambios de Security (ES256 vs HS256)

Viste que cambiaste `security.py` a usar ES256 con JWKS. Eso es **correcto**:

```python
# OLD (HS256 - simétrica, no recomendado):
jwt.decode(token, settings.supabase_anon_key, algorithms=["HS256"])

# NEW (ES256 + JWKS - asimétrica, seguro):
jwks = get_jwks()  # Fetch public keys
key = next(k for k in jwks["keys"] if k["kid"] == token_kid)
jwt.decode(token, key, algorithms=["ES256"])
```

**Ventajas ES256:**
- ✓ Supabase firma con clave privada
- ✓ Tú verificas con clave pública
- ✓ Imposible forjar tokens

---

## Próximos Pasos

1. **Ejecuta el test script:**
   ```bash
   python scripts/test_auth.py
   ```

2. **Si falla, revisa:**
   - `.env` - credenciales correctas
   - Logs del backend (busca `DEBUG:`)
   - GuíaSOLUCION en `docs/SUPABASE_TROUBLESHOOTING.md`

3. **Si funciona:**
   - Comparte el token con el frontend
   - Frontend debe usarlo en `Authorization: Bearer <token>`
   - Prueba acceder a `/api/v1/chats`

4. **Asegúrate que el frontend:**
   - ✓ Llama al endpoint `/auth/signup` o `/auth/login`
   - ✓ Guarda el `access_token`
   - ✓ Lo incluye en todas las requests: `Authorization: Bearer <token>`
   - ✓ Maneja errores (401 = login needed, 409 = email exists)

---

## Contacto & Debug

### Si aún tienes problemas:

1. **Revisa los logs del backend:**
   - Terminal donde corre uvicorn
   - Busca líneas con `DEBUG:`

2. **Lee los docs:**
   - [SUPABASE_TROUBLESHOOTING.md](./docs/SUPABASE_TROUBLESHOOTING.md)
   - [AUTHENTICATION_SOLUTION.md](./docs/AUTHENTICATION_SOLUTION.md)

3. **Ejecuta test:**
   ```bash
   python scripts/test_auth.py
   ```

4. **Verifica Supabase:**
   - Dashboard: https://app.supabase.com/
   - Status: https://status.supabase.com/

---

## Resumen de Cambios de Archivos

| Archivo | Cambio | Impacto |
|---------|--------|--------|
| `auth.py` | Mejor manejo de errores | Errores claros + debugging |
| `security.py` | ES256 + JWKS | ✓ Más seguro (ya hecho) |
| `test_auth.py` | Timeout +3x, mejor logging | Tests más confiables |
| `SUPABASE_TROUBLESHOOTING.md` | Nuevo doc completo | Guía de debug |

Todos listos para que funcione el fullstack! 🚀
