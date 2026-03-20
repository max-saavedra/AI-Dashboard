# Troubleshooting Supabase Authentication Issues

## Problem: Timeout (60000ms exceeded)

### ¿Qué significa?
El frontend está esperando respuesta del backend por más de 60 segundos sin recibirla.

### Causas Comunes

#### 1. Credenciales de Supabase Incorrectas
**Síntomas:**
- Timeout en signup/login
- 400 Bad Request: "Email already registered"
- Errores genéricos vagos

**Solución:**
```bash
# Verificar en .env:
SUPABASE_URL=https://yrenqasaehjoxzzoxqgr.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

- ✓ URL debe ser exacta
- ✓ ANON_KEY debe ser la clave anónima (NO la service role key)
- ✓ No debe tener espacios adicionales

#### 2. Problema de Red/Firewall
**Síntomas:**
- Timeout en cualquier hora
- No puede conectarse a Supabase

**Solución:**
```bash
# Probar conectividad a Supabase
ping yrenqasaehjoxzzoxqgr.supabase.co

# O con curl
curl -I https://yrenqasaehjoxzzoxqgr.supabase.co/auth/v1/.well-known/jwks.json
```

Si no funciona:
- Verificar firewall
- Verificar VPN
- Verificar DNS

#### 3. Conflicto de Email
**Síntomas:**
- Status 400: "Email already registered"
- O timeout mientras valida

**Solución:**
```bash
# Usar un email único (con timestamp)
test1234567890@example.com  # ✓ Será único

# O usar dominios de test
test+unique@example.com
```

#### 4. Credenciales Supabase Expiradas o No Configuradas
**Síntomas:**
- Timeout inmediato
- Backend logs muestran JWKS fetch error

**Solución:**
```python
# Verificar en app/core/security.py
JWKS_URL = f"{settings.supabase_url}/auth/v1/.well-known/jwks.json"
# Debe ser: https://yrenqasaehjoxzzoxqgr.supabase.co/auth/v1/.well-known/jwks.json
```

---

## Step-by-Step Debug Guide

### 1. Verificar Backend Logs
```bash
# Terminal donde corre uvicorn, buscar:
DEBUG: Starting JWT validation
DEBUG: Calling Supabase sign_up
DEBUG: Supabase sign_up response received
```

Si ves timeout, el problema es antes de Supabase.

### 2. Probar Supabase Directamente
```bash
# Test 1: ¿Supabase está online?
curl -I https://yrenqasaehjoxzzoxqgr.supabase.co/auth/v1/.well-known/jwks.json

# Test 2: ¿Puedes conectarte?
python -c "import requests; print(requests.get('https://yrenqasaehjoxzzoxqgr.supabase.co/auth/v1/.well-known/jwks.json').status_code)"
```

### 3. Probar Cliente Supabase
```python
# test_supabase_client.py
from supabase import create_client
from app.core.config import get_settings

settings = get_settings()
supabase = create_client(settings.supabase_url, settings.supabase_anon_key)

# Intenta sign up
response = supabase.auth.sign_up({
    "email": "test@example.com",
    "password": "TestPassword123!"
})

print(f"User: {response.user}")
print(f"Session: {response.session}")
```

### 4. Revisar Logs del Backend
```bash
# En terminal de uvicorn, busca estos mensajes y qué dicen:

# Malo (timeout o hang):
DEBUG: Calling Supabase sign_up
# ... sin más logs por 60 segundos ...

# Bueno (error pero responde rápido):
DEBUG: Calling Supabase sign_up
DEBUG: Signup failed, error_code=email_already_registered
```

---

## Checklist de Configuración

- [ ] `.env` tiene `SUPABASE_URL` correcto
- [ ] `.env` tiene `SUPABASE_ANON_KEY` correcto (no service role)
- [ ] Backend puede resolver DNS (conectarse a internet)
- [ ] Supabase project está active (no suspended)
- [ ] Supabase authentication está habilitado
- [ ] Email verification NO está requerido (o uses email de test)

---

## Configuración Correcta de Supabase

### En Supabase Dashboard

1. **Authentication** → **Providers**
   - ✓ Email oAuth debe estar habilitado
   - ✓ "Confirm email" puede estar ON u OFF (depende tu caso de uso)

2. **Authentication** → **Policies**
   - ✓ Revisar que users pueda registrarse

3. **Settings** → **API**
   - ✓ `anon` (public) key para frontend/backend
   - ✓ `service_role` key para operaciones del servidor

---

## Problemas Específicos & Soluciones

### "Email already registered"
```
✗ Status: 400
✗ Detail: Failed to create account. Email may already be registered.
```

**Causas:**
- Email existe en Supabase (prueba con email con timestamp)
- Base de datos/usuarios duplicados

**Solución:**
```python
import time
email = f"test{int(time.time())}@example.com"
```

### "Request timeout"
```
✗ Status: 504
✗ ErrorCode: timeout
```

**Causas:**
- Supabase tardó más de 30 segundos
- Problema de red
- Credenciales inválidas (Supabase rechaza lentamente)

**Solución:**
1. Aumentar timeout en auth.py:
```python
async with httpx.AsyncClient(timeout=60.0) as client:
```

2. Revisar status de Supabase: https://status.supabase.com/

3. Probar desde otra red

### "JWKS fetch error"
```
DEBUG: JWT validation failed
error_type=RequestError
```

**Causas:**
- No hay conexión a internet
- JWKS URL es incorrecta
- Firewall bloquea requests a Supabase

**Solución:**
```bash
# Test directo
curl -I https://yrenqasaehjoxzzoxqgr.supabase.co/auth/v1/.well-known/jwks.json
```

---

## Testing Real-World Scenarios

### Test 1: Signup nuevo usuario
```bash
python scripts/test_auth.py
```

Debe completarse en < 30 segundos.

### Test 2: Login con credenciales invalidas
```bash
# Crear request manualmente
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"wrong@example.com","password":"wrong"}'

# Esperado: 401 Unauthorized - rápidamente
```

### Test 3: JWKS fetch
```python
from app.core.security import get_jwks
keys = get_jwks()
print(keys)  # Debe imprimir keys, no error
```

---

## Información Útil

### URLs de Supabase
```
Project URL: https://yrenqasaehjoxzzoxqgr.supabase.co
API Endpoint: https://yrenqasaehjoxzzoxqgr.supabase.co/rest/v1
Auth: https://yrenqasaehjoxzzoxqgr.supabase.co/auth/v1
JWKS: https://yrenqasaehjoxzzoxqgr.supabase.co/auth/v1/.well-known/jwks.json (cached)
```

### Backend Supabase Client Initialization
```python
# Current in auth.py (line 21-25):
supabase: Client = create_client(
    settings.supabase_url,
    settings.supabase_anon_key,
    options={
        "http2": False,  # Para evitar problemas de compatibilidad
    }
)
```

---

## Cuando Todo Falla

### Nuclear Option: Reset Supabase
Si nada funciona, en Supabase dashboard:
1. Go to **Settings** → **Database** → **Backups**
2. Reset database (option available)
3. O crear nuevo proyecto

### Opción: Usar Auth externo
Si Supabase no es viable:
- JWT manual (sin provider externo)
- Auth0
- Firebase
- Otro provider OAuth

---

## Performance Tips

Para acelerar signup/login:

```python
# En auth.py, usar sesiones HTTP reutilizables:
client = httpx.AsyncClient(timeout=30.0)

# En lugar de crear nuevo client cada vez
async with httpx.AsyncClient() as client:
    # ...
```

---

## Contact & Support

- Supabase Docs: https://supabase.com/docs
- Supabase Discord: https://discord.supabase.io
- Status Page: https://status.supabase.com
- Log issues: Check uvicorn terminal output

Usa `DEBUG:` logs en backend para troubleshooting.
