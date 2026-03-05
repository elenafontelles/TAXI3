# Plan de Remediacion - TAXI2
# Auditoria: 2026-03-05
# Contexto: VPS con acceso SSH limitado a 2 personas (Ivan + Elena)

---

## Contexto y Asunciones

- VPS privado, solo 2 usuarios SSH
- No hay red compartida (rebaja riesgo de Docker ports expuestos en dev)
- La app gestiona datos fiscales reales de 3 taxis + datos personales de conductores
- Aplica GDPR/LOPD por datos de conductores y geolocalización
- El mayor riesgo real: compromiso de credenciales de plataformas (Uber/FreeNow/Prima)
  y perdida de datos fiscales

---

## FASE 1: Urgente (hacer esta semana)
> Cosas que se arreglan rapido y eliminan los riesgos mas graves

### 1.1 Login API: credenciales fuera de query params
**Riesgo:** Las passwords aparecen en logs del servidor web
**Archivo:** `src/routes/api_v1.py` lineas 38-40
**Cambio:**
```python
# ANTES (MAL)
@router.post("/auth/login")
async def api_login(
    email: str = Query(...),
    password: str = Query(...),
):

# DESPUES (BIEN)
from pydantic import BaseModel

class LoginRequest(BaseModel):
    email: str
    password: str

@router.post("/auth/login")
async def api_login(body: LoginRequest):
    email = body.email
    password = body.password
```
**Esfuerzo:** 10 minutos

---

### 1.2 CI/CD: no interpolar secretos en shell
**Riesgo:** Command injection + tokens en logs
**Archivo:** `.github/workflows/deploy.yml`
**Cambio:**
```yaml
# ANTES (MAL)
script: |
  echo '${{ secrets.GITHUB_TOKEN }}' | sudo docker login ghcr.io ...

# DESPUES (BIEN)
- name: Deploy
  uses: appleboy/ssh-action@v1
  with:
    host: ${{ secrets.VPS_HOST }}
    username: ${{ secrets.VPS_USER }}
    key: ${{ secrets.SSH_PRIVATE_KEY }}
    # QUITAR password - usar solo SSH key
    envs: GITHUB_TOKEN
    script: |
      echo "$GITHUB_TOKEN" | docker login ghcr.io -u x --password-stdin
      cd /ruta/app
      git pull origin main
      docker compose -f docker-compose.prod.yml up -d --build
```
Tambien: quitar `SECRET_KEY: ci-test-secret-key...` hardcodeada y ponerla como secret del repo.
**Esfuerzo:** 20 minutos

---

### 1.3 Shell injection en run_nightly.sh
**Riesgo:** Ejecucion arbitraria de codigo Python si un scraper devuelve output malicioso
**Archivo:** `scripts/run_nightly.sh` lineas 38-41
**Cambio:**
```bash
# ANTES (MAL)
python -c "
from scripts.send_email import send_alert
send_alert('Nightly Sync Errors', '$ERRORS')
"

# DESPUES (BIEN)
ERRORS="$ERRORS" python -c "
import os
from scripts.send_email import send_alert
send_alert('Nightly Sync Errors', os.environ['ERRORS'])
"
```
**Esfuerzo:** 5 minutos

---

### 1.4 Redis: poner password
**Riesgo:** Cualquier proceso/contenedor accede a Redis sin auth
**Archivos:** `docker-compose.prod.yml` + `src/config.py` + `.env`
**Cambio:**
```yaml
# docker-compose.prod.yml
redis:
  image: redis:7-alpine
  command: redis-server --requirepass ${REDIS_PASSWORD}
```
```bash
# .env
REDIS_PASSWORD=<generar con: openssl rand -hex 32>
REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379
```
**Esfuerzo:** 15 minutos

---

## FASE 2: Importante (hacer en 1-2 semanas)
> Mejoras de defensa en profundidad que reducen impacto si algo falla

### 2.1 Separar claves JWT y cifrado
**Riesgo:** Una clave comprometida lo compromete todo
**Archivos:** `src/config.py`, `src/services/token_encryption.py`, `src/services/auth_service.py`
**Cambio:**
```python
# config.py - anadir nueva variable
ENCRYPTION_KEY: str = ""  # Separada de SECRET_KEY

# token_encryption.py - usar HKDF en vez de SHA-256
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes

def _derive_key(master_key: str) -> bytes:
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b"taxi2-token-encryption-v1",  # fijo, no secreto
        info=b"fernet-key",
    )
    return base64.urlsafe_b64encode(hkdf.derive(master_key.encode()))
```
**Post-cambio:** Re-cifrar todos los tokens existentes con la nueva clave.
**Esfuerzo:** 1-2 horas (incluye migracion de tokens)

---

### 2.2 Reducir JWT a 4 horas + invalidacion por logout
**Archivos:** `src/config.py`, `src/routes/auth.py`
**Cambio:**
```python
# config.py
ACCESS_TOKEN_EXPIRE_MINUTES: int = 240  # 4 horas en vez de 24

# auth.py - anadir logout que borre la cookie
@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")
    return RedirectResponse("/login", status_code=303)
```
Dado que solo sois 2 usuarios + conductores, 4h es practico sin ser excesivo.
**Esfuerzo:** 30 minutos

---

### 2.3 Descifrado fallido: lanzar excepcion en vez de string vacio
**Archivo:** `src/services/token_encryption.py:33-38`
**Cambio:**
```python
# ANTES
except InvalidToken:
    logger.warning("Failed to decrypt token")
    return ""

# DESPUES
except InvalidToken:
    logger.error("Failed to decrypt token - possible key rotation or tampering")
    raise ValueError("Token decryption failed - check ENCRYPTION_KEY")
```
Y manejar la excepcion en los callers mostrando un error claro.
**Esfuerzo:** 30 minutos

---

### 2.4 Quitar sudo del deploy
**Archivo:** `.github/workflows/deploy.yml`
**Cambio en el VPS (una vez):**
```bash
# En el VPS, anadir usuario deploy al grupo docker
sudo usermod -aG docker deploy_user
# Reiniciar sesion
```
Luego quitar `sudo` de todos los comandos en el workflow.
**Esfuerzo:** 15 minutos

---

### 2.5 Dockerfile dev: no ejecutar como root
**Archivo:** `Dockerfile`
**Cambio:** Anadir al final (antes del CMD):
```dockerfile
RUN useradd -m -r appuser && chown -R appuser:appuser /app
USER appuser
```
**Esfuerzo:** 5 minutos

---

## FASE 3: Mejoras (hacer en 1 mes)
> Robustez, cumplimiento GDPR, y buenas practicas

### 3.1 GDPR: Implementar DSR (Data Subject Requests)
El modelo `DsrRequest` existe pero no hace nada. Necesita:
- Endpoint para que un conductor solicite acceso/borrado de sus datos
- Servicio que ejecute el borrado en cascada (trips, fuel_expenses, shifts, etc.)
- Export de datos en JSON/CSV para portabilidad
- Tracking del plazo de 30 dias

**Esfuerzo:** 4-6 horas

### 3.2 GDPR: Ampliar anonimizacion mas alla de GPS
- Anonimizar datos de conductores inactivos tras X meses
- Politica de retencion para datos de viajes (mas alla de los 90 dias de GPS)
- Documentar las politicas en un registro de tratamiento

**Esfuerzo:** 2-3 horas

### 3.3 Backups automaticos de PostgreSQL
```bash
# Anadir al crontab del VPS
0 3 * * * docker exec taxi2-db pg_dump -U taxi_admin taxi_api | \
  gzip > /backups/taxi_$(date +\%Y\%m\%d).sql.gz

# Retener 30 dias
0 4 * * * find /backups -name "taxi_*.sql.gz" -mtime +30 -delete
```
**Esfuerzo:** 30 minutos

### 3.4 CSV formula injection en exports
**Archivo:** `src/routes/export.py`
**Cambio:** Sanitizar valores antes de escribir CSV:
```python
def sanitize_csv_value(value):
    if isinstance(value, str) and value and value[0] in ('=', '+', '-', '@', '\t'):
        return "'" + value
    return value
```
**Esfuerzo:** 20 minutos

### 3.5 Validacion de uploads (extension + tamano)
**Archivo:** `src/routes/upload.py`
```python
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls", ".pdf"}

content = await csv_file.read()
if len(content) > MAX_UPLOAD_SIZE:
    raise HTTPException(413, "Archivo demasiado grande (max 10MB)")
ext = Path(csv_file.filename).suffix.lower()
if ext not in ALLOWED_EXTENSIONS:
    raise HTTPException(400, f"Extension no permitida: {ext}")
```
**Esfuerzo:** 15 minutos

### 3.6 PII fuera del codigo fuente
**Archivo:** `scripts/parsers/prima_parser.py:49-53`
Mover `_CONDUCTOR_MAP` a variable de entorno o tabla en base de datos.
**Esfuerzo:** 20 minutos

---

## FASE 4: Cuando haya tiempo
> Nice-to-have que mejoran la postura general

| Tarea | Esfuerzo |
|-------|----------|
| Migrar de `python-jose` a `PyJWT` | 1 hora |
| Anadir CSRF tokens reales a formularios | 2 horas |
| Rate limiting con Redis (no in-memory) | 30 min |
| Anadir `iss`/`aud` claims al JWT | 20 min |
| Security headers middleware (HSTS, X-Content-Type-Options) | 15 min |
| Healthcheck para el worker en docker-compose.prod | 15 min |
| Quitar `root_path` del endpoint /health | 5 min |
| Politica de complejidad de passwords | 30 min |

---

## Resumen de Esfuerzo

| Fase | Tiempo estimado | Plazo |
|------|----------------|-------|
| Fase 1 (Urgente) | ~50 minutos | Esta semana |
| Fase 2 (Importante) | ~4-5 horas | 1-2 semanas |
| Fase 3 (Mejoras) | ~8-10 horas | 1 mes |
| Fase 4 (Nice-to-have) | ~5 horas | Cuando se pueda |

**Total: ~18-20 horas de trabajo** para remediar toda la auditoria.

---

## Nota sobre el Contexto VPS (2 personas)

Lo que este contexto REBAJA:
- Docker ports expuestos en dev (no hay red compartida)
- Dashboard visible a todos (sois pocos)
- CSRF (no hay usuarios maliciosos internos)

Lo que este contexto NO REBAJA:
- CI/CD secrets (GitHub Actions es publico/compartido)
- Credenciales de plataformas (Uber/FreeNow compromise afecta al negocio)
- GDPR (aplica independientemente del tamano)
- Backups (una VPS es un single point of failure)
- Shell injection en nightly (un scraper externo podria devolver datos maliciosos)
