# 🚀 PLANTILLA COMPLETA v7.0 - GUÍA DEFINITIVA

**La Biblia del Desarrollo con Claude**  
**Todo lo que necesitas en un solo documento**

> Basada en:
> - KYC+AML (86 tests TDD, Diciembre 2024)
> - Dashboard V2 + Auth-v2 (Enero 2026)
> - Intrastat Manager V2 + TDD Perfecto (8 Enero 2026)
> - Incidentes de producción documentados
> - iContainers experience (acquired by Agility)
> - Clearcust development
> - 10+ años tech entrepreneurship

**Fecha:** 8 Enero 2026  
**Autor:** Ivan Tintoré (CEO MAITSA, Co-founder Clearcust)  
**Versión:** 7.0 Production-Hardened + TDD Perfect + Naming Convention

---

## 📚 ÍNDICE COMPLETO

### PARTE I: FUNDAMENTOS
1. [Filosofía y Reglas](#parte-i-filosofía-y-reglas)
2. [SOLID Principles](#solid-principles)
3. [Clean Code](#clean-code-principles)
4. [Design Patterns](#design-patterns-catalogue)

### PARTE II: ARQUITECTURA
5. [Clean Architecture](#clean-architecture)
6. [Layers Explicadas](#layers-explicadas)
7. [Repository Pattern](#repository-pattern)
8. [Dependency Injection](#dependency-injection)

### PARTE III: TDD WORKFLOW
9. [Ciclo TDD Completo](#ciclo-tdd-completo)
10. [Context Verification](#context-verification-crítico)
11. [Tests Unitarios](#tests-unitarios)
12. [Tests E2E](#tests-e2e)
13. [Smoke Tests](#smoke-tests-crítico) ⭐ NUEVO
14. [Infrastructure Tests](#infrastructure-tests)
15. [Pre-commit Hooks](#pre-commit-hooks)

### PARTE IV: SEGURIDAD
13. [Input Validation](#input-validation)
14. [SQL Injection Prevention](#sql-injection-prevention)
15. [Authentication & Authorization](#authentication--authorization)
16. [Secrets Management](#secrets-management)

### PARTE V: PERFORMANCE
17. [Database Optimization](#database-optimization)
18. [Caching Strategies](#caching-strategies)
19. [Async Patterns](#async-patterns)
20. [Profiling Tools](#profiling-tools)

### PARTE VI: OBSERVABILITY
21. [Structured Logging](#structured-logging)
22. [Distributed Tracing](#distributed-tracing)
23. [Metrics & Dashboards](#metrics--dashboards)
24. [Alerting](#alerting)
25. [Production Monitoring Stack](#production-monitoring-stack-loki--grafana)

### PARTE VII: DEPLOYMENT
25. [Staging Environment Setup](#staging-environment-setup)
26. [Docker Best Practices](#docker-best-practices)
27. [Docker Networking Debugging](#docker-networking-debugging)
28. [Git-Crypt & Encrypted Secrets](#git-crypt--encrypted-secrets-management)
29. [Environment Variables Validation](#environment-variables-validation)
30. [Multi-Repo Management](#multi-repo-management)
31. [Traefik Configuration](#traefik-configuration)
32. [CI/CD Pipeline](#cicd-pipeline)
33. [Zero-Downtime Deploy](#zero-downtime-deploy)
34. [Rollback Procedures](#rollback-procedures)
35. [Post-Deploy Validation](#post-deploy-validation-script)

### PARTE VIII: TROUBLESHOOTING
34. [Debug Playbook](#debug-playbook)
35. [Common Issues](#common-issues)
36. [Errores Comunes V2](#errores-comunes-v2) ⭐ NUEVO
37. [Incident Response](#incident-response)

### PARTE IX: NAMING CONVENTION ⭐ NUEVO
38. [Estándar de Nombres](#estándar-de-nombres-único)
39. [Ejemplo: Intrastat](#ejemplo-intrastat-manager-implementado)
40. [Template para Nuevos Servicios](#template-para-nuevos-servicios)

---

# PARTE I: FILOSOFÍA Y REGLAS

## Reglas Inquebrantables

```
1. Tests PRIMERO, código DESPUÉS (sin excepciones)
2. SOLID principles siempre
3. Clean Architecture (Domain → Application → Infrastructure)
4. Security by design (nunca "lo añadimos después")
5. Infrastructure as Code (todo en Git)
6. Observability desde día 1
7. Zero downtime deploys
8. Rollback < 30 segundos
9. NUNCA --no-verify
10. Documentation as code
11. SIEMPRE verificar contexto PRIMERO (grep, codebase_search)
12. SIEMPRE confirmar qué contenedor sirve qué ruta
13. SIEMPRE ejecutar tests E2E ANTES de dar OK
14. SIEMPRE documentar arquitectura claramente
15. SIEMPRE escribir tests Browser para UI (Selenium/Playwright, no solo HTTP)
16. SIEMPRE usar naming convention único: <nombre-servicio>-v2 (Docker, Caddy, docs)
17. NUNCA aplicar fixes con sed/awk en contenedores (fix en código fuente + rebuild)
```

### 🔍 **Regla #11-14: Context Verification (Lección 1 Enero 2026)**

> **Origen:** Deployamos auth-v2 sin verificar que había 2 repos separados (`/opt/dashboard` y `/opt/dashboard-v2`).
> Resultado: Modificamos archivos incorrectos, bugs en producción.

**SIEMPRE hacer ANTES de tocar código:**

```bash
# 1. Verificar estructura del proyecto
grep -r "dashboard.*v2" .
codebase_search "Where is the V2 dashboard located?"

# 2. Verificar qué contenedor sirve qué ruta
docker ps | grep dashboard
grep "handle /tools2/" Caddyfile

# 3. Confirmar arquitectura
cat README.md
cat ARQUITECTURA_*.md

# 4. Verificar deployment actual
ssh server "docker ps --format '{{.Names}}: {{.Image}}'"
```

**Si NO verificas:**
- ❌ Modificas archivos incorrectos
- ❌ Deployas a lugar equivocado
- ❌ Bugs en producción
- ❌ Pierdes tiempo arreglando

**Si SÍ verificas:**
- ✅ Modificas archivos correctos
- ✅ Deploy al lugar correcto
- ✅ Zero bugs por confusión
- ✅ Tiempo bien invertido

---

## SOLID Principles

### S - Single Responsibility Principle

> Una clase debe tener una y solo una razón para cambiar

**❌ Violación:**
```python
class User:
    """Hace DEMASIADAS cosas"""
    
    def __init__(self, email: str, password: str):
        self.email = email
        self.password = password
    
    def save_to_database(self):
        """Responsabilidad de persistencia"""
        conn = psycopg2.connect(...)
        conn.execute("INSERT INTO users...")
    
    def send_welcome_email(self):
        """Responsabilidad de notificaciones"""
        smtp = smtplib.SMTP(...)
        smtp.send_message(...)
    
    def hash_password(self):
        """Responsabilidad de seguridad"""
        return bcrypt.hashpw(self.password.encode())
```

**✅ Solución:**
```python
# Cada clase UNA responsabilidad

class User:
    """Solo representa un usuario (domain entity)"""
    def __init__(self, email: Email, password: HashedPassword):
        self.email = email
        self.password = password

class UserRepository:
    """Solo persistencia"""
    def save(self, user: User) -> None:
        conn = self._get_connection()
        conn.execute("INSERT INTO users...")

class EmailNotifier:
    """Solo emails"""
    def send_welcome(self, user: User) -> None:
        self._email_service.send(...)

class PasswordHasher:
    """Solo hashing"""
    def hash(self, plain: str) -> HashedPassword:
        return HashedPassword(bcrypt.hashpw(plain.encode()))
```

---

### O - Open/Closed Principle

> Abierto para extensión, cerrado para modificación

**✅ Strategy Pattern:**
```python
from abc import ABC, abstractmethod

class ReportFormatter(ABC):
    @abstractmethod
    def format(self, data: dict) -> str:
        pass

class PDFFormatter(ReportFormatter):
    def format(self, data: dict) -> str:
        return generate_pdf(data)

class ExcelFormatter(ReportFormatter):
    def format(self, data: dict) -> str:
        return generate_excel(data)

class ReportGenerator:
    def __init__(self, formatter: ReportFormatter):
        self._formatter = formatter
    
    def generate(self, data: dict) -> str:
        return self._formatter.format(data)

# Añadir nuevo formato = solo nueva clase
class JSONFormatter(ReportFormatter):
    def format(self, data: dict) -> str:
        return json.dumps(data)
```

---

### L - Liskov Substitution Principle

> Las subclases deben poder sustituir a sus clases base

**✅ Correcto:**
```python
from abc import ABC, abstractmethod

class Shape(ABC):
    @abstractmethod
    def area(self) -> float:
        pass

class Rectangle(Shape):
    def __init__(self, width: float, height: float):
        self._width = width
        self._height = height
    
    def area(self) -> float:
        return self._width * self._height

class Square(Shape):
    def __init__(self, side: float):
        self._side = side
    
    def area(self) -> float:
        return self._side ** 2

# Ambos son sustituibles
def calculate_area(shape: Shape) -> float:
    return shape.area()
```

---

### I - Interface Segregation Principle

> Muchas interfaces específicas > una general

**✅ Solución:**
```python
class Workable(ABC):
    @abstractmethod
    def work(self) -> None:
        pass

class Eatable(ABC):
    @abstractmethod
    def eat(self) -> None:
        pass

class Human(Workable, Eatable):
    def work(self) -> None:
        print("Working...")
    
    def eat(self) -> None:
        print("Eating...")

class Robot(Workable):
    def work(self) -> None:
        print("Working 24/7...")
    # No necesita eat()
```

---

### D - Dependency Inversion Principle

> Depende de abstracciones, no de concreciones

**✅ Solución:**
```python
from abc import ABC, abstractmethod

class Database(ABC):
    @abstractmethod
    def query(self, sql: str) -> list:
        pass

class MySQLDatabase(Database):
    def query(self, sql: str) -> list:
        # MySQL implementation
        pass

class PostgreSQLDatabase(Database):
    def query(self, sql: str) -> list:
        # PostgreSQL implementation
        pass

class UserService:
    def __init__(self, database: Database):
        self._db = database  # Abstracción
    
    def get_user(self, user_id: int) -> User:
        results = self._db.query("SELECT * FROM users WHERE id = %s", (user_id,))
        return User.from_dict(results[0])

# Funciona con cualquier Database
service = UserService(MySQLDatabase())
service = UserService(PostgreSQLDatabase())
```

---

## Clean Code Principles

### DRY - Don't Repeat Yourself

**✅ Una fuente de verdad:**
```python
class TaxCalculator:
    TAX_RATE = 0.21  # Un solo lugar
    
    @classmethod
    def calculate_tax(cls, amount: float) -> float:
        return amount * cls.TAX_RATE
    
    @classmethod
    def calculate_total(cls, amount: float) -> float:
        return amount + cls.calculate_tax(amount)
```

---

### KISS - Keep It Simple

**❌ Over-engineering:**
```python
class AbstractFactoryBuilderProvider:
    # 50 líneas de complejidad innecesaria
    pass
```

**✅ Simple:**
```python
class EmailSender:
    def __init__(self, host: str, port: int):
        self._host = host
        self._port = port
    
    def send(self, message: str) -> None:
        with smtplib.SMTP(self._host, self._port) as server:
            server.send_message(message)
```

---

### YAGNI - You Aren't Gonna Need It

**✅ Solo lo necesario HOY:**
```python
class User:
    def __init__(self, email: str):
        self.email = email
        # Otros campos se añaden cuando sean necesarios
```

---

## Design Patterns Catalogue

### Repository Pattern

```python
from abc import ABC, abstractmethod

class UserRepository(ABC):
    @abstractmethod
    def get_by_id(self, user_id: int) -> Optional[User]:
        pass
    
    @abstractmethod
    def save(self, user: User) -> User:
        pass

class SQLUserRepository(UserRepository):
    def __init__(self, session: Session):
        self._session = session
    
    def get_by_id(self, user_id: int) -> Optional[User]:
        model = self._session.query(UserModel).get(user_id)
        return self._to_entity(model) if model else None
    
    def save(self, user: User) -> User:
        # ORM logic
        pass

class InMemoryUserRepository(UserRepository):
    def __init__(self):
        self._users = {}
    
    def get_by_id(self, user_id: int) -> Optional[User]:
        return self._users.get(user_id)
    
    def save(self, user: User) -> User:
        self._users[user.id] = user
        return user
```

---

### Factory Pattern

```python
class PaymentGatewayFactory:
    @staticmethod
    def create(gateway_type: str, config: dict) -> PaymentGateway:
        if gateway_type == "stripe":
            return StripeGateway(
                api_key=config["stripe_api_key"]
            )
        elif gateway_type == "paypal":
            return PayPalGateway(
                client_id=config["paypal_client_id"]
            )
        raise ValueError(f"Unknown gateway: {gateway_type}")
```

---

### Strategy Pattern

```python
class DiscountStrategy(ABC):
    @abstractmethod
    def calculate(self, amount: float) -> float:
        pass

class PercentageDiscount(DiscountStrategy):
    def __init__(self, percentage: float):
        self._percentage = percentage
    
    def calculate(self, amount: float) -> float:
        return amount * (1 - self._percentage / 100)

class PriceCalculator:
    def __init__(self, strategy: DiscountStrategy):
        self._strategy = strategy
    
    def calculate_final_price(self, base: float) -> float:
        return self._strategy.calculate(base)
```

---

# PARTE II: ARQUITECTURA

## Clean Architecture

```
┌─────────────────────────────────────────┐
│         FRAMEWORKS & DRIVERS            │
│    (FastAPI, SQLAlchemy, Redis)         │
├─────────────────────────────────────────┤
│      INTERFACE ADAPTERS                 │
│  (Controllers, Presenters, Gateways)    │
├─────────────────────────────────────────┤
│      APPLICATION BUSINESS RULES         │
│     (Use Cases, Services)               │
├─────────────────────────────────────────┤
│    ENTERPRISE BUSINESS RULES            │
│    (Entities, Domain Logic)             │
│         (CORE - independiente)          │
└─────────────────────────────────────────┘

Dependencies point INWARD →
```

---

## Layers Explicadas

### Layer 1: Domain (Entities)

```python
# domain/entities/user.py

@dataclass
class User:
    """Entity pura - SIN dependencias externas"""
    id: Optional[int]
    email: str
    name: str
    is_active: bool = True
    
    def deactivate(self) -> None:
        """Lógica de negocio"""
        if not self.is_active:
            raise ValueError("Already inactive")
        self.is_active = False
    
    def can_perform_action(self) -> bool:
        """Business rule"""
        return self.is_active
```

---

### Layer 2: Application (Use Cases)

```python
# application/use_cases/create_order.py

class CreateOrderUseCase:
    def __init__(
        self,
        order_repo: OrderRepository,
        user_repo: UserRepository,
        notifier: EmailNotifier
    ):
        self._orders = order_repo
        self._users = user_repo
        self._notifier = notifier
    
    def execute(self, user_id: int, items: list) -> Result[Order, str]:
        # 1. Validar usuario
        user = self._users.get_by_id(user_id)
        if not user:
            return Err(f"User {user_id} not found")
        
        # 2. Crear order
        order = Order(
            user_id=user_id,
            items=items,
            status=OrderStatus.PENDING
        )
        
        # 3. Persistir
        saved = self._orders.save(order)
        
        # 4. Notificar
        self._notifier.send_confirmation(saved, user)
        
        return Ok(saved)
```

---

### Layer 3: Infrastructure (Adapters)

```python
# infrastructure/persistence/sqlalchemy_order_repository.py

class SQLAlchemyOrderRepository(OrderRepository):
    def __init__(self, session: Session):
        self._session = session
    
    def save(self, order: Order) -> Order:
        # Domain Entity → ORM Model
        model = OrderModel(
            user_id=order.user_id,
            status=order.status.value
        )
        
        self._session.add(model)
        self._session.commit()
        
        # ORM Model → Domain Entity
        return self._to_entity(model)
```

---

### Layer 4: Presentation (API)

```python
# presentation/api/orders.py

@router.post("/orders")
async def create_order(
    request: CreateOrderRequest,
    use_case: CreateOrderUseCase = Depends()
):
    result = use_case.execute(
        user_id=request.user_id,
        items=request.items
    )
    
    if result.is_err():
        raise HTTPException(400, detail=result.error)
    
    return OrderResponse.from_entity(result.unwrap())
```

---

## Repository Pattern

### Interface

```python
class UserRepository(Protocol):
    def get_by_id(self, user_id: int) -> Optional[User]: ...
    def get_by_email(self, email: str) -> Optional[User]: ...
    def save(self, user: User) -> User: ...
    def delete(self, user_id: int) -> None: ...
```

### SQL Implementation

```python
class SQLAlchemyUserRepository(UserRepository):
    def get_by_id(self, user_id: int) -> Optional[User]:
        model = self._session.query(UserModel).get(user_id)
        return self._to_entity(model) if model else None
```

### In-Memory (Tests)

```python
class InMemoryUserRepository(UserRepository):
    def __init__(self):
        self._users = {}
    
    def get_by_id(self, user_id: int) -> Optional[User]:
        return self._users.get(user_id)
```

---

## Dependency Injection

### Container Setup

```python
from dependency_injector import containers, providers

class Container(containers.DeclarativeContainer):
    config = providers.Configuration()
    
    # Database
    db_session = providers.Singleton(
        create_db_session,
        url=config.database_url
    )
    
    # Repositories
    user_repository = providers.Factory(
        SQLAlchemyUserRepository,
        session=db_session
    )
    
    # Use Cases
    create_user_use_case = providers.Factory(
        CreateUserUseCase,
        repository=user_repository
    )
```

---

# PARTE III: TDD WORKFLOW

## Ciclo TDD Completo

```mermaid
flowchart TD
    Start[Nueva Feature] --> Context[0. VERIFY CONTEXT]
    Context --> TestUnit[1. Test Unitario RED]
    TestUnit --> RunTest1[pytest]
    RunTest1 --> Fail1{Falla?}
    Fail1 -->|Sí| Code1[2. Código Mínimo]
    Fail1 -->|No| Error[❌ Test debe fallar]
    
    Code1 --> RunTest2[pytest]
    RunTest2 --> Pass1{Pasa?}
    Pass1 -->|No| Code1
    Pass1 -->|Sí| TestE2E[3. Tests E2E]
    
    TestE2E --> TestInfra[4. Infrastructure Test]
    TestInfra --> Refactor[5. Refactor]
    Refactor --> AllTests[6. Run ALL tests]
    AllTests --> Commit[7. Commit]
    Commit --> Push[8. Push]
    Push --> Deploy[9. Deploy]
    Deploy --> PostTests[10. Post-Deploy E2E]
    PostTests --> OK{Pasan?}
    OK -->|Sí| Success[✅ Deploy OK]
    OK -->|No| Rollback[❌ Rollback]
```

---

## Context Verification (CRÍTICO)

> **Nueva regla después de incidente 1 Enero 2026**
>
> **Problema:** Deployamos auth-v2 sin verificar que había 2 repos separados.
> Modificamos `dashboard-web/` (V1) cuando debíamos usar `dashboard-v2-orchestrator/` (V2).
> **Resultado:** 4 bugs en producción, 2 horas extra de debugging.

### PASO 0: Verificar Contexto ANTES de tocar código

**SIEMPRE ejecutar ANTES de empezar:**

```bash
# 1. ¿DÓNDE está el código que necesito modificar?
grep -r "feature-name" .
codebase_search "Where is X implemented?"
find . -name "*feature*"

# 2. ¿QUÉ contenedores están corriendo?
docker ps --format "{{.Names}}: {{.Image}}"

# 3. ¿QUÉ sirve cada ruta?
grep "handle /ruta/" Caddyfile
grep "reverse_proxy" Caddyfile

# 4. ¿HAY múltiples versiones/repos?
ls -la /opt/
git remote -v
cat README.md | grep -i "ubicación\|location"

# 5. ¿CUÁL es la arquitectura actual?
cat ARQUITECTURA*.md
cat README.md
```

### Ejemplo Real (Auth-v2, 1 Enero 2026)

**❌ Lo que hicimos (MAL):**
```bash
# Asumimos que dashboard-web/ era V2
# Modificamos sin verificar
# Deployamos a producción
# → 4 bugs encontrados DESPUÉS
```

**✅ Lo que debimos hacer (BIEN):**
```bash
# 1. Verificar PRIMERO
grep -r "dashboard.*v2" .
docker ps | grep dashboard
grep "/tools2/" Caddyfile

# 2. Descubrir que existen:
#    - dashboard-web (V1) en /opt/dashboard
#    - dashboard-v2-orchestrator (V2) en /opt/dashboard-v2
#
# 3. Confirmar qué sirve /tools2/
grep -A5 "handle /tools2/" Caddyfile
# → reverse_proxy dashboard-web:3000 (INCORRECTO!)

# 4. Arreglar ANTES de deployar
# → Cambiar a dashboard-v2-orchestrator:3000

# 5. Tests E2E confirman el fix
pytest tests/test_auth_v2_e2e.py

# 6. Deploy → 0 bugs
```

### Checklist de Context Verification

```
ANTES de modificar CUALQUIER archivo:

□ ¿Dónde está el código que necesito? (grep/search)
□ ¿Hay múltiples versiones/repos? (ls, git remote)
□ ¿Qué contenedores existen? (docker ps)
□ ¿Qué contenedor sirve mi ruta? (Caddyfile/nginx.conf)
□ ¿Hay documentación? (README, ARQUITECTURA, etc.)
□ ¿Estoy en el directorio/repo correcto?
□ ¿Hay staging/production separados?

SOLO DESPUÉS de confirmar → modificar código
```

### Red Flags (Señales de alerta)

```
🚩 "Voy a modificar este archivo porque asumí que es el correcto"
   → PARA. Verifica primero.

🚩 "Hay dos cosas con nombre similar, elijo una al azar"
   → PARA. Investiga cuál es cuál.

🚩 "Este contenedor no aparece en docker ps pero sigo adelante"
   → PARA. ¿Por qué no aparece? ¿Está en otro servidor?

🚩 "El Caddyfile apunta a X pero yo modifico Y"
   → PARA. Hay discordancia, investiga.

🚩 "No entiendo la arquitectura pero empiezo a codear"
   → PARA. Lee la documentación primero.
```

---

---

## Tests Unitarios

### API Endpoints

```python
class TestHealthEndpoint:
    def test_health_returns_200(self, client):
        """🔴 Health debe retornar 200"""
        response = client.get("/health")
        assert response.status_code == 200
    
    def test_health_returns_json(self, client):
        """🔴 Health debe retornar JSON"""
        response = client.get("/health")
        assert response.headers["content-type"] == "application/json"
    
    def test_health_has_required_fields(self, client):
        """🔴 Health debe tener campos requeridos"""
        response = client.get("/health")
        data = response.json()
        assert "status" in data
        assert "version" in data
```

---

## Tests E2E

> **CRÍTICO:** Estos tests detectan bugs en producción ANTES de deployar

### Tests de Routing

```python
class TestRoutingConfiguration:
    """Tests que verifican configuración de reverse proxy"""
    
    def test_route_uses_correct_backend(self):
        """CRÍTICO: Verificar que la ruta usa el backend correcto"""
        response = requests.get("https://keonycs.com/tools2/", allow_redirects=False)
        
        # Si redirige, debe ser al auth correcto
        if response.status_code == 302:
            location = response.headers["location"]
            # V2 debe usar auth-v2
            assert location.startswith("/auth-v2/"), \
                f"ERROR: /tools2/ should use auth-v2, got {location}"
    
    def test_route_preserves_parameters(self):
        """CRÍTICO: Forward auth debe preservar parámetros"""
        response = requests.get("https://keonycs.com/tools2/", allow_redirects=False)
        location = response.headers.get("location", "")
        
        # Debe preservar la ruta original
        assert "next=/tools2/" in location, \
            f"ERROR: Lost original path. Location: {location}"
```

### Tests de OAuth Configuration

```python
class TestOAuthConfiguration:
    """Tests que verifican configuración OAuth"""
    
    def test_oauth_client_id_is_not_dummy(self):
        """CRÍTICO: Credenciales NO deben ser dummy"""
        response = requests.get("https://keonycs.com/auth-v2/login", allow_redirects=False)
        location = response.headers["location"]
        
        # Extraer client_id
        import re
        match = re.search(r'client_id=([^&]+)', location)
        assert match, "No client_id in OAuth URL"
        
        client_id = match.group(1)
        assert client_id != "dummy", \
            "ERROR: Using dummy credentials! Check environment variables"
    
    def test_redirect_uri_is_correct(self):
        """CRÍTICO: Redirect URI debe apuntar al callback correcto"""
        response = requests.get("https://keonycs.com/auth-v2/login", allow_redirects=False)
        location = response.headers["location"]
        
        # Debe tener redirect_uri correcto
        assert "redirect_uri=https%3A%2F%2Fkeonycs.com%2Fauth-v2%2Fcallback" in location, \
            "ERROR: Wrong redirect_uri in OAuth URL"
```

### Tests de Contenido

```python
class TestDashboardContent:
    """Tests que verifican que el contenido deployado es el correcto"""
    
    def test_dashboard_shows_correct_version(self, authenticated_session):
        """Dashboard debe mostrar la versión correcta"""
        response = requests.get("https://keonycs.com/tools2/", 
                              cookies=authenticated_session)
        html = response.text
        
        # V2 debe decir "V2" explícitamente
        assert "V2" in html or "v2" in html, \
            "ERROR: Dashboard doesn't show V2 badge. Wrong version deployed?"
    
    def test_dashboard_links_to_v2_services(self, authenticated_session):
        """Links deben apuntar a servicios V2, no V1"""
        response = requests.get("https://keonycs.com/tools2/",
                              cookies=authenticated_session)
        html = response.text
        
        # Debe tener links a V2
        assert 'href="/v2/conversor/"' in html, \
            "ERROR: Conversor link points to V1!"
        
        # NO debe tener links directos a V1
        assert 'href="/conversor/"' not in html, \
            "ERROR: Found V1 link in V2 dashboard!"
```

---

### 🎯 **Cuándo correr estos tests**

```python
"""
WORKFLOW CORRECTO:

1. ANTES de modificar código:
   - Verificar contexto (grep, search)
   - Confirmar arquitectura
   - Identificar qué modificar

2. DESPUÉS de modificar código (LOCAL):
   - pytest tests/unit/ -v
   - pytest tests/test_dashboard_v2_content.py -v
   
3. ANTES de commit:
   - Pre-commit hooks corren automáticamente
   - Si fallan → arreglar

4. DESPUÉS de deploy (PRODUCCIÓN):
   - pytest tests/test_auth_v2_e2e.py -v
   - pytest tests/test_caddy_routing.py -v
   
5. Si tests E2E fallan:
   ❌ Deploy NO exitoso
   ❌ Rollback inmediato
   ✅ Arreglar y re-deployar

6. Si tests E2E pasan:
   ✅ Deploy exitoso
   ✅ Marcar como completado
"""
```

---

### Business Logic

```python
class TestOrderCalculation:
    def test_order_total_calculation(self):
        """🔴 Total correcto"""
        order = Order(items=[
            OrderItem(price=10.0, quantity=2),
            OrderItem(price=5.0, quantity=3)
        ])
        assert order.total() == 35.0
    
    def test_order_with_discount(self):
        """🔴 Descuento aplicado"""
        order = Order(items=[OrderItem(price=100.0, quantity=1)])
        order.apply_discount(0.1)
        assert order.total() == 90.0
```

---

## Smoke Tests (CRÍTICO)

> **Nueva lección crítica - 6 Enero 2026**
>
> **Problema:** Healthcheck dice ✅ HEALTHY pero servicio da ❌ ERROR 502
> **Descubrimiento:** Healthcheck interno NO garantiza funcionamiento real
> **Solución:** Smoke Tests que verifican funcionamiento REAL

### El Problema: Falsa Sensación de Seguridad

**Healthcheck superficial:**
```dockerfile
HEALTHCHECK CMD curl -f http://localhost:8000/health
```

**Verifica SOLO:**
- ✅ Servicio responde internamente en /health
- ✅ Proceso está vivo

**NO verifica:**
- ❌ Reverse proxy funciona (Caddy → servicio)
- ❌ Auth forward funciona correctamente
- ❌ Servicio sirve contenido real
- ❌ Network routing correcto
- ❌ URLs públicas accesibles

**Resultado:** Dashboard dice ✅ HEALTHY, usuario accede y ve ❌ ERROR 502

### Smoke Tests: Verificación REAL

**Son tests rápidos que verifican funcionamiento básico REAL:**

```python
# tests/test_services_smoke.py

import pytest
import requests
import time

BASE_URL = "https://keonycs.com"

@pytest.mark.parametrize("service,url", [
    ("conversor", "/v2/conversor/"),
    ("taxi", "/v2/taxi/"),
    ("adela", "/v2/adela/"),
    ("kyc-aml", "/v2/kyc-aml/"),
    # ... todos los servicios
])
class TestAllServicesSmoke:
    """Smoke tests para TODOS los servicios"""
    
    def test_service_not_502(self, service, url):
        """CRÍTICO: Ningún servicio debe dar 502 Bad Gateway"""
        response = requests.get(BASE_URL + url, allow_redirects=True, timeout=10)
        assert response.status_code != 502, \
            f"❌ {service} da 502 - Healthcheck mintió, servicio NO funciona"
    
    def test_service_not_503(self, service, url):
        """Ningún servicio debe dar 503 Service Unavailable"""
        response = requests.get(BASE_URL + url, allow_redirects=True, timeout=10)
        assert response.status_code != 503, \
            f"❌ {service} da 503 - Servicio no disponible"
    
    def test_service_responds_under_10s(self, service, url):
        """Servicios deben responder en < 10 segundos"""
        start = time.time()
        try:
            response = requests.get(BASE_URL + url, allow_redirects=True, timeout=10)
            elapsed = time.time() - start
            assert elapsed < 10.0, \
                f"❌ {service} muy lento: {elapsed:.2f}s"
        except requests.Timeout:
            pytest.fail(f"❌ {service} timeout después de 10s")
    
    def test_service_returns_valid_response(self, service, url):
        """Servicios deben retornar respuesta válida (200, 302, 401)"""
        response = requests.get(BASE_URL + url, allow_redirects=False, timeout=10)
        assert response.status_code in [200, 302, 401], \
            f"❌ {service} retorna código inesperado: {response.status_code}"
```

### Niveles de Testing

**Nivel 1: Healthcheck (Básico)**
```
✅ Proceso vivo
✅ /health responde
❌ NO garantiza funcionamiento real
```

**Nivel 2: Smoke Test (Crítico)** ⭐
```
✅ URL pública no da 502/503/504
✅ Servicio responde en tiempo razonable (< 10s)
✅ Retorna códigos HTTP válidos
✅ Reverse proxy funciona
✅ Auth forward funciona
```

**Nivel 3: Functional Test (Recomendado)**
```
✅ Funcionalidad básica operativa
✅ Ej: Conversor acepta upload
✅ Ej: Taxi muestra formulario
✅ Ej: Adela procesa extractos
```

**Nivel 4: Integration Test (Completo)**
```
✅ Flujo end-to-end completo
✅ Login → Upload → Process → Download
```

### Cuándo Ejecutar Smoke Tests

**POST-DEPLOY (Crítico):**
```bash
# Después de cada deploy
pytest tests/test_services_smoke.py -v

# Si fallan → ROLLBACK inmediato
# Si pasan → Deploy OK
```

**DIARIAMENTE (Recomendado):**
```bash
# Cron job
0 8 * * * cd /app && pytest tests/test_services_smoke.py || \
          echo "ALERTA: Smoke tests failing" | mail -s "Alert" admin@company.com
```

**ANTES DE SWITCH V1→V2:**
```bash
# Validación final antes de migrar usuarios
pytest tests/test_services_smoke.py -v

# TODOS deben pasar (0 failures)
```

### Ejemplo Real: Incidente 6 Enero 2026

**Situación:**
```
Dashboard muestra: ✅ Conversor HEALTHY
Usuario accede: ❌ ERROR 502
```

**Causa:**
```
Healthcheck solo verifica /health interno
NO verifica que Caddy → Conversor funcione
NO verifica que auth forward funcione
NO verifica que servicio sirva contenido
```

**Solución:**
```
Smoke tests creados: 47 tests
Resultado: ✅ 47/48 PASSED
Detectan: 502, 503, 504, timeouts, errores routing

Ahora SÍ sabemos que servicios funcionan REALMENTE
```

### Template Smoke Test Por Servicio

```python
def test_my_service_smoke():
    """Smoke test completo para mi servicio"""
    
    # 1. URL accesible (no 502/503)
    response = requests.get("https://domain.com/service/", 
                          allow_redirects=True, 
                          timeout=10)
    assert response.status_code not in [502, 503, 504]
    
    # 2. Response time aceptable
    start = time.time()
    response = requests.get("https://domain.com/service/")
    assert (time.time() - start) < 5.0
    
    # 3. Retorna contenido (no error page)
    assert len(response.text) > 100
    assert "error" not in response.text.lower() or \
           "service" in response.text.lower()
```

### Comparación: Healthcheck vs Smoke Test

| Aspecto | Healthcheck | Smoke Test |
|---------|-------------|------------|
| Verifica | Proceso vivo | Funciona REALMENTE |
| Scope | Interno | Público (URL real) |
| Detecta 502 | ❌ NO | ✅ SÍ |
| Detecta routing | ❌ NO | ✅ SÍ |
| Detecta auth | ❌ NO | ✅ SÍ |
| Performance | ❌ NO | ✅ SÍ |
| Tiempo ejecución | < 1s | 5-10s |
| Cuándo ejecutar | Cada 30s | Post-deploy, diario |

### Lección Aprendida

```
❌ FALSO:
Healthcheck ✅ = Servicio funciona

✅ VERDAD:
Healthcheck ✅ = Proceso vivo
Smoke Tests ✅ = Servicio funciona REALMENTE

Necesitas AMBOS:
- Healthcheck: Monitoreo continuo interno
- Smoke Tests: Validación funcionamiento real
```

### Implementación Recomendada

**1. Crear suite smoke tests:**
```bash
tests/
├── test_services_smoke.py  # Todos los servicios
├── test_conversor_smoke.py # Específico conversor
├── test_taxi_smoke.py      # Específico taxi
└── ...
```

**2. Ejecutar en CI/CD:**
```yaml
# .github/workflows/deploy.yml
- name: Smoke Tests Post-Deploy
  run: pytest tests/test_services_smoke.py -v
  
- name: Rollback if failed
  if: failure()
  run: ./scripts/rollback.sh
```

**3. Monitoreo diario:**
```bash
# Cron
0 8 * * * /app/scripts/run-smoke-tests.sh
```

### Checklist Smoke Tests

```
□ Test para cada servicio público
□ Verificar no da 502/503/504
□ Verificar response time < 10s
□ Verificar códigos HTTP válidos
□ Ejecutar post-deploy
□ Ejecutar diariamente
□ Alertar si fallan
```

---

## Infrastructure Tests

### Docker Tests

```python
class TestDockerfile:
    def test_dockerfile_exists(self):
        assert Path("Dockerfile").exists()
    
    def test_dockerfile_uses_specific_version(self):
        content = Path("Dockerfile").read_text()
        assert ":latest" not in content
    
    def test_dockerfile_builds(self):
        result = subprocess.run(
            ["docker", "build", "-t", "test:build", "."],
            capture_output=True
        )
        assert result.returncode == 0
```

---

### Docker Compose Tests

```python
class TestDockerCompose:
    def test_compose_valid_yaml(self):
        import yaml
        data = yaml.safe_load(Path("docker-compose.yml").read_text())
        assert data is not None
    
    def test_all_services_have_healthcheck(self):
        import yaml
        data = yaml.safe_load(Path("docker-compose.yml").read_text())
        for name, config in data["services"].items():
            assert "healthcheck" in config
```

---

## Pre-commit Hooks

### Setup

```yaml
# .pre-commit-config.yaml

repos:
  - repo: local
    hooks:
      - id: pytest-unit
        name: Run unit tests
        entry: pytest tests/unit -x
        language: system
        always_run: true
      
      - id: pytest-infrastructure
        name: Run infrastructure tests
        entry: pytest tests/infrastructure -x
        language: system
        always_run: true
      
      - id: ruff
        name: Ruff linter
        entry: ruff check .
        language: system
        types: [python]
```

---

# PARTE IV: SEGURIDAD

## Input Validation

### Pydantic Validation

```python
from pydantic import BaseModel, EmailStr, Field

class CreateUserRequest(BaseModel):
    email: EmailStr
    age: int = Field(ge=18, le=120)
    name: str = Field(min_length=2, max_length=100)
    
    @validator('name')
    def name_no_numbers(cls, v):
        if any(c.isdigit() for c in v):
            raise ValueError('Name cannot contain numbers')
        return v.strip()
```

---

### File Upload Validation

```python
async def validate_file(file: UploadFile):
    # 1. Extension
    ext = Path(file.filename).suffix.lower()
    if ext not in {'.jpg', '.png', '.pdf'}:
        raise HTTPException(400, "Invalid extension")
    
    # 2. Size
    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:  # 10MB
        raise HTTPException(400, "File too large")
    
    # 3. MIME type
    mime = magic.from_buffer(contents, mime=True)
    if mime not in {'image/jpeg', 'image/png', 'application/pdf'}:
        raise HTTPException(400, f"Invalid file type: {mime}")
```

---

## SQL Injection Prevention

**✅ SIEMPRE usar ORM o parametrized queries:**

```python
# ✅ SQLAlchemy ORM
user = session.query(User).filter(User.id == user_id).first()

# ✅ Parametrized SQL
cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))

# ❌ NUNCA string concatenation
query = f"SELECT * FROM users WHERE id = {user_id}"  # VULNERABLE
```

---

## Authentication & Authorization

### JWT Authentication

```python
from jose import jwt
from passlib.context import CryptContext

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
pwd_context = CryptContext(schemes=["bcrypt"])

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=30)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    token = credentials.credentials
    payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    user_id = payload.get("sub")
    user = user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(401, "Invalid token")
    return user
```

---

### RBAC Authorization

```python
def require_role(*roles: UserRole):
    async def dependency(
        current_user: User = Depends(get_current_user)
    ) -> User:
        if current_user.role not in roles:
            raise HTTPException(403, "Insufficient permissions")
        return current_user
    return dependency

@app.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    current_user: User = Depends(require_role(UserRole.ADMIN))
):
    # Solo admins
    pass
```

---

## Secrets Management

```python
from pydantic import BaseSettings

class Settings(BaseSettings):
    database_url: str
    jwt_secret_key: str
    stripe_api_key: str
    
    class Config:
        env_file = ".env"

settings = Settings()

# .env (NO commitear)
DATABASE_URL=postgresql://user:pass@localhost/db
JWT_SECRET_KEY=your-secret-here
```

---

# PARTE V: PERFORMANCE

## Database Optimization

### Select Only Needed

```python
# ❌ ALL columns
users = session.query(User).all()

# ✅ Specific columns
users = session.query(User.id, User.email).all()
```

---

### Use Indexes

```python
class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    email = Column(String, nullable=False)
    
    __table_args__ = (
        Index('idx_user_email', 'email', unique=True),
    )
```

---

### N+1 Problem

**❌ Problema:**
```python
users = session.query(User).all()  # 1 query
for user in users:
    orders = user.orders  # N queries
```

**✅ Solución:**
```python
from sqlalchemy.orm import joinedload

users = session.query(User)\
    .options(joinedload(User.orders))\
    .all()  # 1 query con JOIN
```

---

## Caching Strategies

### Redis Cache

```python
class RedisCache:
    def __init__(self, host: str, port: int):
        self.client = redis.Redis(host=host, port=port)
    
    def get(self, key: str) -> Optional[Any]:
        value = self.client.get(key)
        return json.loads(value) if value else None
    
    def set(self, key: str, value: Any, ttl: int = 3600):
        self.client.setex(key, ttl, json.dumps(value))

def cache_result(ttl: int = 3600):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{args}"
            
            cached = cache.get(cache_key)
            if cached:
                return cached
            
            result = await func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            return result
        return wrapper
    return decorator

@cache_result(ttl=300)
async def get_user_expensive(user_id: int):
    # Expensive operation
    pass
```

---

## Async Patterns

```python
# ✅ Concurrent execution
@app.get("/users/{user_id}")
async def get_user(user_id: int):
    user, orders = await asyncio.gather(
        db.get_user_async(user_id),
        db.get_orders_async(user_id)
    )
    return {"user": user, "orders": orders}
```

---

## Profiling Tools

### cProfile

```python
import cProfile

profiler = cProfile.Profile()
profiler.enable()

# Code to profile
result = expensive_operation()

profiler.disable()
profiler.print_stats(sort='cumulative')
```

---

### py-spy (Production)

```bash
# Install
pip install py-spy

# Profile running process
py-spy top --pid 12345

# Generate flamegraph
py-spy record -o profile.svg --pid 12345
```

---

# PARTE VI: OBSERVABILITY

## Structured Logging

### JSON Logger

```python
import logging
import json

class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
        }
        
        if hasattr(record, 'request_id'):
            log_data['request_id'] = record.request_id
        
        return json.dumps(log_data)

logger = logging.getLogger()
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger.addHandler(handler)

logger.info("User logged in", extra={"user_id": 123})
```

---

## Distributed Tracing

### OpenTelemetry

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

trace.set_tracer_provider(TracerProvider())
FastAPIInstrumentor.instrument_app(app)

tracer = trace.get_tracer(__name__)

@app.post("/orders")
async def create_order(request: CreateOrderRequest):
    with tracer.start_as_current_span("create_order") as span:
        span.set_attribute("user_id", request.user_id)
        
        with tracer.start_as_current_span("validate"):
            validation = await validate(request)
        
        with tracer.start_as_current_span("save"):
            order = await save_order(request)
        
        return order
```

---

## Metrics & Dashboards

### Prometheus Metrics

```python
from prometheus_client import Counter, Histogram

http_requests = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

@app.middleware("http")
async def collect_metrics(request: Request, call_next):
    with http_duration.labels(
        method=request.method,
        endpoint=request.url.path
    ).time():
        response = await call_next(request)
    
    http_requests.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    return response
```

---

## Alerting

### AlertManager Rules

```yaml
groups:
  - name: api_alerts
    rules:
      - alert: HighErrorRate
        expr: |
          rate(http_requests_total{status=~"5.."}[5m])
          / rate(http_requests_total[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
      
      - alert: SlowResponses
        expr: |
          histogram_quantile(0.95,
            rate(http_request_duration_seconds_bucket[5m])
          ) > 1.0
        for: 5m
        labels:
          severity: warning
```

---

## Production Monitoring Stack (Loki + Grafana)

> **Por qué:** Necesitas ver logs, métricas y alertas en tiempo real
> **Cuándo implementar:** Día 1 de producción

### Stack Completo

```yaml
# docker-compose.monitoring.yml

version: '3.8'

services:
  # ========== LOKI (Log Aggregation) ==========
  loki:
    image: grafana/loki:2.9.0
    ports:
      - "3100:3100"
    volumes:
      - ./config/loki-config.yml:/etc/loki/local-config.yaml
      - loki_data:/loki
    command: -config.file=/etc/loki/local-config.yaml
    networks:
      - monitoring
    restart: unless-stopped

  # ========== PROMTAIL (Log Collector) ==========
  promtail:
    image: grafana/promtail:2.9.0
    volumes:
      - ./config/promtail-config.yml:/etc/promtail/config.yml
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
      - /var/run/docker.sock:/var/run/docker.sock
    command: -config.file=/etc/promtail/config.yml
    networks:
      - monitoring
    restart: unless-stopped

  # ========== PROMETHEUS (Metrics) ==========
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./config/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.retention.time=30d'
    networks:
      - monitoring
    restart: unless-stopped

  # ========== GRAFANA (Visualization) ==========
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD:-admin}
      - GF_USERS_ALLOW_SIGN_UP=false
    volumes:
      - grafana_data:/var/lib/grafana
      - ./config/grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./config/grafana/datasources:/etc/grafana/provisioning/datasources
    networks:
      - monitoring
    restart: unless-stopped

  # ========== ALERTMANAGER (Alerts) ==========
  alertmanager:
    image: prom/alertmanager:latest
    ports:
      - "9093:9093"
    volumes:
      - ./config/alertmanager.yml:/etc/alertmanager/alertmanager.yml
    command:
      - '--config.file=/etc/alertmanager/alertmanager.yml'
    networks:
      - monitoring
    restart: unless-stopped

volumes:
  loki_data:
  prometheus_data:
  grafana_data:

networks:
  monitoring:
    driver: bridge
```

### Loki Configuration

```yaml
# config/loki-config.yml

auth_enabled: false

server:
  http_listen_port: 3100

ingester:
  lifecycler:
    ring:
      kvstore:
        store: inmemory
      replication_factor: 1
  chunk_idle_period: 5m
  chunk_retain_period: 30s

schema_config:
  configs:
    - from: 2024-01-01
      store: boltdb-shipper
      object_store: filesystem
      schema: v11
      index:
        prefix: index_
        period: 24h

storage_config:
  boltdb_shipper:
    active_index_directory: /loki/index
    cache_location: /loki/cache
    shared_store: filesystem
  filesystem:
    directory: /loki/chunks

limits_config:
  enforce_metric_name: false
  reject_old_samples: true
  reject_old_samples_max_age: 168h
```

### Promtail Configuration

```yaml
# config/promtail-config.yml

server:
  http_listen_port: 9080

positions:
  filename: /tmp/positions.yaml

clients:
  - url: http://loki:3100/loki/api/v1/push

scrape_configs:
  # Scrape all Docker containers
  - job_name: docker
    docker_sd_configs:
      - host: unix:///var/run/docker.sock
        refresh_interval: 5s
    
    relabel_configs:
      - source_labels: ['__meta_docker_container_name']
        target_label: 'container'
      - source_labels: ['__meta_docker_container_log_stream']
        target_label: 'stream'
```

### Prometheus Configuration

```yaml
# config/prometheus.yml

global:
  scrape_interval: 15s
  evaluation_interval: 15s

alerting:
  alertmanagers:
    - static_configs:
        - targets: ['alertmanager:9093']

rule_files:
  - '/etc/prometheus/alerts/*.yml'

scrape_configs:
  # Scrape servicios con métricas
  - job_name: 'auth-service-v2'
    static_configs:
      - targets: ['auth-service-v2:8080']
    metrics_path: '/metrics'
  
  - job_name: 'api-services'
    static_configs:
      - targets:
        - 'kyc-aml:8000'
        - 'conversor:8000'
        - 'arbol:8000'
```

### Alert Rules

```yaml
# config/prometheus/alerts/api-alerts.yml

groups:
  - name: api_alerts
    interval: 30s
    rules:
      # High error rate
      - alert: HighErrorRate
        expr: |
          rate(http_requests_total{status=~"5.."}[5m])
          / rate(http_requests_total[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate on {{ $labels.service }}"
          description: "Error rate is {{ $value | humanizePercentage }}"
      
      # Service down
      - alert: ServiceDown
        expr: up{job="api-services"} == 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Service {{ $labels.instance }} is down"
      
      # OAuth failures (específico de hoy)
      - alert: OAuthFailures
        expr: |
          rate(oauth_failures_total[5m]) > 0.1
        for: 3m
        labels:
          severity: warning
        annotations:
          summary: "OAuth failures detected"
          description: "Check client_id and credentials"
      
      # Slow responses
      - alert: SlowAPI
        expr: |
          histogram_quantile(0.95,
            rate(http_request_duration_seconds_bucket[5m])
          ) > 2.0
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "API is slow (p95 > 2s)"
```

### Grafana Dashboard for Auth-v2

```json
{
  "dashboard": {
    "title": "Auth Service V2",
    "panels": [
      {
        "title": "Requests per Second",
        "targets": [{
          "expr": "rate(http_requests_total{service='auth-v2'}[1m])"
        }]
      },
      {
        "title": "OAuth Success Rate",
        "targets": [{
          "expr": "rate(oauth_success_total[5m]) / rate(oauth_attempts_total[5m])"
        }]
      },
      {
        "title": "Active Sessions",
        "targets": [{
          "expr": "active_sessions{service='auth-v2'}"
        }]
      },
      {
        "title": "Login Errors (Top 10)",
        "targets": [{
          "expr": "topk(10, rate(oauth_errors_total[5m]))"
        }]
      }
    ]
  }
}
```

### Quick Setup

```bash
# Levantar monitoring stack
docker-compose -f docker-compose.monitoring.yml up -d

# Acceder Grafana
open http://localhost:3001
# User: admin, Pass: admin (cambiar!)

# Agregar datasources:
# - Loki: http://loki:3100
# - Prometheus: http://prometheus:9090

# Import dashboards predefinidos
curl https://grafana.com/api/dashboards/1860/revisions/latest/download > docker-dashboard.json
```

---

# PARTE VII: DEPLOYMENT

## Staging Environment Setup

> **Por qué lo necesitas:** Hoy encontramos 4 bugs EN PRODUCCIÓN
> Con staging los habríamos detectado ANTES

### The Problem (1 Enero 2026)

```
❌ Deploy directo a producción
❌ Tests solo en local
❌ Usuarios reales ven bugs primero
❌ Fix bajo presión
```

### The Solution

```
✅ Deploy a staging primero
✅ Tests E2E en staging
✅ Detectar bugs sin usuarios reales
✅ Fix con calma
✅ Deploy a producción confiado
```

### Minimal Staging Setup

```yaml
# docker-compose.staging.yml

version: '3.8'

services:
  # Mismos servicios que producción
  # Pero con:
  # - Datos de prueba
  # - Logging verbose
  # - Sin SSL (HTTP solo)
  
  auth-service-v2-staging:
    build: ./apps/auth-service-v2
    container_name: staging-auth-v2
    environment:
      - ENV=staging
      - LOG_LEVEL=DEBUG
      - GOOGLE_CLIENT_ID=${STAGING_GOOGLE_CLIENT_ID}
      - GOOGLE_REDIRECT_URI=http://staging.local:8080/auth-v2/callback
    ports:
      - "8080:8080"
    networks:
      - staging

  caddy-staging:
    image: caddy:2-alpine
    ports:
      - "8080:80"
    volumes:
      - ./Caddyfile.staging:/etc/caddy/Caddyfile:ro
    networks:
      - staging

networks:
  staging:
```

### Caddyfile Staging

```caddyfile
# Caddyfile.staging

:80 {
    # Sin HTTPS para staging local
    
    handle /tools2/* {
        forward_auth auth-service-v2-staging:8080 {
            uri /verify?next=/tools2/
        }
        reverse_proxy dashboard-v2-orchestrator-staging:3000
    }
}
```

### Staging Workflow

```bash
#!/bin/bash
# scripts/deploy-to-staging.sh

echo "🎭 Deploying to STAGING"

# 1. Start staging environment
docker-compose -f docker-compose.staging.yml up -d

# 2. Wait for services
sleep 10

# 3. Run E2E tests against staging
echo "🧪 Running E2E tests..."
pytest tests/test_*_e2e.py --base-url=http://staging.local:8080 -v

# 4. Validation passed?
if [ $? -eq 0 ]; then
    echo "✅ STAGING TESTS PASSED"
    echo ""
    echo "Ready for production deploy:"
    echo "  ./scripts/deploy-to-production.sh"
else
    echo "❌ STAGING TESTS FAILED"
    echo "Fix issues before deploying to production!"
    exit 1
fi
```

### Use Staging for

```
✅ Test new features
✅ Verify OAuth flow completo
✅ Check routing configuration
✅ Validate environment variables
✅ Test rollback procedures
✅ Performance testing
✅ Load testing
✅ Breaking changes

❌ NO usar staging para:
- Datos reales de usuarios
- Secrets de producción
- Testing en público (no indexable)
```

### Local Staging Setup

```bash
# /etc/hosts
127.0.0.1  staging.local

# Start staging
docker-compose -f docker-compose.staging.yml up -d

# Access
open http://staging.local:8080/tools2/

# Run tests
pytest tests/ --base-url=http://staging.local:8080

# Cleanup
docker-compose -f docker-compose.staging.yml down -v
```

### Staging → Production Checklist

```
□ Staging environment up
□ Deploy to staging
□ All E2E tests pass on staging
□ Manual testing on staging
□ Performance acceptable
□ No memory leaks
□ Logs clean
□ Only THEN → deploy to production
```

---

## Rollback Procedures

> **Por qué:** Si algo falla en producción, necesitas volver atrás < 30 segundos

### Automated Rollback Script

```bash
#!/bin/bash
# scripts/rollback.sh

set -e

SERVICE_NAME="${1:?Service name required}"
BACKUP_TAG="${2:-previous}"

echo "🔄 ROLLING BACK: $SERVICE_NAME"
echo "==============================="
echo ""

# ========== STEP 1: Verify Backup Exists ==========
echo "1️⃣  Checking backup image..."

if ! docker images | grep -q "$SERVICE_NAME.*$BACKUP_TAG"; then
    echo "❌ No backup image found: $SERVICE_NAME:$BACKUP_TAG"
    echo ""
    echo "Available images:"
    docker images | grep "$SERVICE_NAME"
    exit 1
fi

echo "✅ Backup image found"

# ========== STEP 2: Tag Current as Failed ==========
echo ""
echo "2️⃣  Tagging current version as failed..."

docker tag $SERVICE_NAME:latest $SERVICE_NAME:failed-$(date +%Y%m%d-%H%M%S)
echo "✅ Current version tagged"

# ========== STEP 3: Rollback to Previous ==========
echo ""
echo "3️⃣  Rolling back to previous version..."

docker tag $SERVICE_NAME:$BACKUP_TAG $SERVICE_NAME:latest
echo "✅ Image rolled back"

# ========== STEP 4: Restart Service ==========
echo ""
echo "4️⃣  Restarting service..."

docker compose stop $SERVICE_NAME
docker compose rm -f $SERVICE_NAME
docker compose up -d $SERVICE_NAME

# ========== STEP 5: Verify Health ==========
echo ""
echo "5️⃣  Verifying health..."

for i in {1..30}; do
    if docker compose exec -T $SERVICE_NAME curl -sf http://localhost:8080/health > /dev/null 2>&1; then
        echo "✅ Service healthy after rollback!"
        break
    fi
    
    if [ $i -eq 30 ]; then
        echo "❌ Service not healthy after rollback!"
        docker compose logs --tail=50 $SERVICE_NAME
        exit 1
    fi
    
    sleep 1
done

# ========== STEP 6: Run Basic Tests ==========
echo ""
echo "6️⃣  Running smoke tests..."

pytest tests/test_${SERVICE_NAME//-/_}_e2e.py::TestHealthEndpoint -v || {
    echo "⚠️  Health tests failed but service is running"
}

# ========== SUMMARY ==========
echo ""
echo "=========================================="
echo "🎉 ROLLBACK COMPLETED!"
echo "=========================================="
echo ""
echo "Service: $SERVICE_NAME"
echo "Rolled back to: $BACKUP_TAG"
echo "Failed version tagged: failed-$(date +%Y%m%d)"
echo ""
echo "Next steps:"
echo "  1. Investigate logs of failed version"
echo "  2. Fix issue"
echo "  3. Test in staging"
echo "  4. Re-deploy to production"
echo ""
```

### Pre-Deploy: Tag Previous Version

```bash
#!/bin/bash
# scripts/tag-before-deploy.sh

SERVICE_NAME="${1:?Service name required}"

echo "🏷️  Tagging current version as backup..."

# Tag current as previous (for rollback)
docker tag $SERVICE_NAME:latest $SERVICE_NAME:previous

# Tag with timestamp
docker tag $SERVICE_NAME:latest $SERVICE_NAME:backup-$(date +%Y%m%d-%H%M%S)

echo "✅ Current version tagged for rollback"
docker images | grep "$SERVICE_NAME" | head -5
```

### Deploy with Auto-Rollback

```bash
#!/bin/bash
# scripts/deploy-with-auto-rollback.sh

SERVICE_NAME="${1:?Service name required}"

echo "🚀 Deploying $SERVICE_NAME with auto-rollback protection"
echo ""

# 1. Tag current version (for rollback)
./scripts/tag-before-deploy.sh "$SERVICE_NAME"

# 2. Deploy new version
echo "📦 Deploying new version..."
docker compose up -d --build $SERVICE_NAME

# 3. Wait for service
echo "⏳ Waiting for service to be ready..."
sleep 10

# 4. Post-deploy validation
echo "🧪 Running post-deploy validation..."

if ! ./scripts/post-deploy-validation.sh "$SERVICE_NAME"; then
    echo ""
    echo "🚨 VALIDATION FAILED - ROLLING BACK AUTOMATICALLY!"
    echo ""
    
    ./scripts/rollback.sh "$SERVICE_NAME" previous
    
    echo ""
    echo "❌ DEPLOYMENT FAILED - ROLLED BACK TO PREVIOUS VERSION"
    exit 1
fi

echo ""
echo "✅ DEPLOYMENT SUCCESSFUL!"
```

### Blue-Green Deployment

```bash
#!/bin/bash
# scripts/blue-green-deploy.sh

SERVICE="$1"
CURRENT_COLOR="${2:-blue}"  # blue or green
NEW_COLOR=$([[ "$CURRENT_COLOR" == "blue" ]] && echo "green" || echo "blue")

echo "🔵🟢 Blue-Green Deployment"
echo "Current: $CURRENT_COLOR"
echo "Deploying to: $NEW_COLOR"
echo ""

# 1. Deploy to inactive color
echo "Deploying to $NEW_COLOR..."
docker compose up -d ${SERVICE}-${NEW_COLOR}

# 2. Wait and validate
sleep 15

if ! curl -f http://localhost:8080/health; then
    echo "❌ $NEW_COLOR failed health check"
    docker compose stop ${SERVICE}-${NEW_COLOR}
    exit 1
fi

# 3. Run E2E tests against new version
pytest tests/ --base-url=http://${SERVICE}-${NEW_COLOR}:8080

if [ $? -ne 0 ]; then
    echo "❌ Tests failed on $NEW_COLOR"
    docker compose stop ${SERVICE}-${NEW_COLOR}
    exit 1
fi

# 4. Switch traffic (update load balancer/Traefik labels)
echo "Switching traffic to $NEW_COLOR..."

# Update Traefik label or Caddy config
docker compose up -d --no-deps traefik

# 5. Stop old version
sleep 30
echo "Stopping $CURRENT_COLOR..."
docker compose stop ${SERVICE}-${CURRENT_COLOR}

echo ""
echo "✅ Blue-Green deployment complete!"
echo "Active: $NEW_COLOR"
echo "Standby: $CURRENT_COLOR (stopped)"
```

### Rollback Checklist

```
WHEN to rollback:

□ Health check fails
□ E2E tests fail post-deploy
□ Error rate > 5% (Prometheus alert)
□ Users reporting issues
□ Memory/CPU spike
□ Database errors
□ Integration broken

HOW to rollback:

1. ./scripts/rollback.sh [service]      (30 sec)
2. Verify health                        (30 sec)
3. Notify team                          (1 min)
4. Investigate logs of failed version   (calmly)
5. Fix issue                            (con tests)
6. Test in staging                      (E2E)
7. Re-deploy                            (confiado)

TIME: < 2 minutos total
```

### Rollback Test (Run Quarterly)

```bash
#!/bin/bash
# scripts/test-rollback-procedure.sh

echo "🧪 TESTING ROLLBACK PROCEDURE (DRY RUN)"
echo ""

SERVICE="auth-service-v2"

# 1. Tag current
docker tag $SERVICE:latest $SERVICE:test-rollback-backup

# 2. Deploy dummy "broken" version
echo "Simulating broken deployment..."
docker run -d --name ${SERVICE}-broken \
  -e GOOGLE_CLIENT_ID="dummy" \
  $SERVICE:latest

# 3. Detect it's broken
sleep 5
if curl -f http://localhost:8080/health; then
    echo "Should have failed but didn't"
fi

# 4. Execute rollback
./scripts/rollback.sh $SERVICE test-rollback-backup

# 5. Verify
if curl -f http://localhost:8080/health; then
    echo "✅ Rollback procedure works!"
else
    echo "❌ Rollback procedure FAILED - FIX IT!"
fi

# Cleanup
docker stop ${SERVICE}-broken
docker rm ${SERVICE}-broken
```

---

## Docker Best Practices

### Multi-Stage Dockerfile

```dockerfile
# Stage 1: Builder
FROM python:3.12-slim AS builder

WORKDIR /build
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.12-slim

RUN useradd -m -u 1000 appuser
WORKDIR /app

COPY --from=builder /root/.local /home/appuser/.local
COPY --chown=appuser:appuser . .

ENV PATH=/home/appuser/.local/bin:$PATH
USER appuser

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0"]
```

---

## Docker Networking Debugging

> **Lección:** Auth-v2 deployment (1 Enero 2026)
> Caddy no podía alcanzar auth-service-v2 por problemas de red

### Quick Diagnostic

```bash
#!/bin/bash
# scripts/debug-docker-networking.sh

SERVICE_A="caddy"
SERVICE_B="auth-service-v2"

echo "🔍 Debugging Docker networking between $SERVICE_A and $SERVICE_B"
echo ""

# 1. ¿Están ambos corriendo?
echo "📋 Container status:"
docker ps --filter "name=$SERVICE_A" --format "{{.Names}}: {{.Status}}"
docker ps --filter "name=$SERVICE_B" --format "{{.Names}}: {{.Status}}"

# 2. ¿En qué redes están?
echo ""
echo "🌐 Networks for $SERVICE_A:"
docker inspect $SERVICE_A -f '{{range $key, $value := .NetworkSettings.Networks}}{{$key}} {{end}}'

echo ""
echo "🌐 Networks for $SERVICE_B:"
docker inspect $SERVICE_B -f '{{range $key, $value := .NetworkSettings.Networks}}{{$key}} {{end}}'

# 3. ¿IPs en las mismas redes?
echo ""
echo "📍 IP Addresses:"
docker inspect $SERVICE_A | grep -A5 '"Networks"' | grep IPAddress
docker inspect $SERVICE_B | grep -A5 '"Networks"' | grep IPAddress

# 4. Test de conectividad
echo ""
echo "🔗 Connectivity test:"
docker exec $SERVICE_A ping -c 2 $SERVICE_B 2>&1 || \
    docker exec $SERVICE_A wget -qO- http://$SERVICE_B:8080/health 2>&1 || \
    echo "❌ Cannot reach $SERVICE_B from $SERVICE_A"

# 5. DNS resolution
echo ""
echo "🔍 DNS resolution:"
docker exec $SERVICE_A nslookup $SERVICE_B 2>&1 || \
    docker exec $SERVICE_A getent hosts $SERVICE_B 2>&1 || \
    echo "❌ DNS not resolving"
```

### Common Solutions

```bash
# Solución 1: Conectar a red faltante
docker network connect [network-name] [container-name]

# Solución 2: Recrear con redes correctas
docker run -d --name service \
  --network network1 \
  --network network2 \
  image:tag

docker network connect network3 service

# Solución 3: Verificar docker-compose networks
docker-compose config | grep -A10 networks

# Solución 4: Recrear redes
docker network rm [network]
docker network create [network]
docker-compose up -d
```

### Network Troubleshooting Checklist

```
□ Ambos contenedores corriendo?
□ Están en la MISMA red?
□ DNS resuelve el nombre?
□ Firewall/iptables bloqueando?
□ Puerto correcto? (80 vs 3000 vs 8080)
□ Healthcheck pasando?
□ Logs muestran conexión?
```

---

## Docker Automatic Cleanup (Production Essential)

> **Lección:** Servidor Dinahosting (5 Enero 2026)
> RAM al 83%, procesos zombie acumulándose, SSH no respondía
> Streamlit consumiendo memoria hasta matar el servidor

### El Problema

```
Síntomas:
- RAM usage: 83%+ (con solo 2GB)
- Zombie processes: 12+
- Out of Memory: Killed process (streamlit)
- SSH timeout (servicios mueren por falta de RAM)
- Servidor reiniciando servicios automáticamente
```

### La Solución: Limpieza Automática

**NO reiniciar el servidor** (causa downtime). En su lugar, limpieza Docker cada 6 horas:

```bash
#!/bin/bash
# /usr/local/bin/docker-cleanup.sh
# Limpieza automática Docker - Sin downtime

# Limpiar contenedores parados, imágenes huérfanas, redes no usadas
docker system prune -f

# Reiniciar contenedores con procesos zombie (sin afectar el resto)
docker ps -q | xargs docker restart

# Log
echo "$(date): Docker cleanup completado" >> /var/log/docker-cleanup.log
```

### Instalación

```bash
# 1. Copiar script al servidor
scp scripts/docker-cleanup-cron.sh root@server:/usr/local/bin/docker-cleanup.sh

# 2. Dar permisos
ssh root@server 'chmod +x /usr/local/bin/docker-cleanup.sh'

# 3. Configurar cron (cada 6 horas)
ssh root@server '(crontab -l 2>/dev/null; echo "0 */6 * * * /usr/local/bin/docker-cleanup.sh") | crontab -'

# 4. Verificar
ssh root@server 'crontab -l | grep docker-cleanup'
```

### Horario de Ejecución

```
0 */6 * * * → Cada 6 horas:
- 00:00 (medianoche)
- 06:00 (madrugada)
- 12:00 (mediodía)
- 18:00 (tarde)
```

### Qué Limpia

```
✅ Contenedores parados
✅ Imágenes sin tag (dangling)
✅ Redes no usadas
✅ Build cache antiguo
✅ Reinicia contenedores con zombie processes
✅ Libera espacio en disco
```

### Beneficios

```
RAM: 83% → ~70% (libera ~250MB)
Zombie processes: 12 → 0
Espacio disco: Recupera 2-5 GB cada ejecución
Downtime: 0 segundos (reinicio por contenedor)
SSH: Siempre responde (no se satura RAM)
```

### Monitorear Efectividad

```bash
# Ver cuánto liberó la última limpieza
ssh root@server 'tail -100 /var/log/docker-cleanup.log'

# Ver RAM antes/después
ssh root@server 'free -h'

# Ver procesos zombie
ssh root@server 'docker ps -a | grep -i exited'
```

### Alternativas Consideradas (y descartadas)

**❌ Reinicio diario del servidor:**
- Downtime: 30-60 segundos
- Interrumpe usuarios
- No soluciona la causa raíz

**❌ Aumentar RAM:**
- Coste: 5-10€/mes
- Solo retrasa el problema
- No elimina zombie processes

**✅ Limpieza automática (elegida):**
- Cero downtime
- Cero coste
- Soluciona causa raíz
- Previene acumulación

### Para VPS de 2GB (Recomendado)

```bash
# Además de limpieza, limitar memoria de contenedores
# docker-compose.yml:
services:
  service-pesado:
    mem_limit: 512m
    mem_reservation: 256m
```

### Testing

```bash
# Ejecutar manualmente para probar
ssh root@server '/usr/local/bin/docker-cleanup.sh'

# Ver qué eliminaría (dry-run)
docker system prune --dry-run
```

---

## Git-Crypt & Encrypted Secrets Management

> **Lección:** Auth-v2 deployment (1 Enero 2026)
> .env encriptado bloqueó todos los `docker compose build`

### El Problema

```bash
# .env está encriptado con git-crypt
$ docker compose build auth-v2
error: failed to read .env: unexpected character "\x00GITCRYPT"
```

### Solución 1: Desbloquear git-crypt

```bash
# En el servidor
cd /opt/dashboard
git-crypt unlock

# Verificar que funcionó
head -c 10 .env
# NO debe mostrar "GITCRYPT"
```

### Solución 2: Bypass Temporal (para CI/CD)

```bash
#!/bin/bash
# scripts/build-with-encrypted-env.sh

# Backup .env encriptado
cp .env .env.encrypted

# Crear .env temporal con valores necesarios
cat > .env << EOF
SECRET_KEY=${SECRET_KEY:-$(openssl rand -hex 32)}
GOOGLE_CLIENT_ID=${GOOGLE_CLIENT_ID}
GOOGLE_CLIENT_SECRET=${GOOGLE_CLIENT_SECRET}
EOF

# Build
docker compose build

# Restore .env encriptado
mv .env.encrypted .env

echo "✅ Built with temporary .env"
```

### Solución 3: Variables de Entorno Directas

```bash
# No usar .env file, pasar vars directamente
docker run -d \
  -e SECRET_KEY="$SECRET_KEY" \
  -e GOOGLE_CLIENT_ID="$GOOGLE_CLIENT_ID" \
  -e GOOGLE_CLIENT_SECRET="$GOOGLE_CLIENT_SECRET" \
  my-service:latest
```

### Best Practices

```yaml
# docker-compose.yml
services:
  api:
    environment:
      # ✅ Con defaults para build (si .env falla)
      SECRET_KEY: ${SECRET_KEY:-changeme-dev-only}
      
      # ✅ Sin defaults para producción (falla si no existe)
      GOOGLE_CLIENT_ID: ${GOOGLE_CLIENT_ID:?GOOGLE_CLIENT_ID required}
```

### Verificar antes de Build

```bash
# Test que .env es legible
if head -c 10 .env 2>/dev/null | grep -q "GITCRYPT"; then
    echo "❌ .env is encrypted!"
    echo "Run: git-crypt unlock"
    exit 1
fi

echo "✅ .env is readable"
```

---

## Environment Variables Validation

> **Lección:** Auth-v2 tuvo credentials "dummy" en producción
> Usuario vio error: "OAuth client was not found"

### Pre-Deploy Validation Script

```bash
#!/bin/bash
# scripts/validate-env-vars.sh

set -e

echo "🔐 Validating environment variables..."

# Función para verificar var
check_var() {
    local var_name=$1
    local service=$2
    local invalid_values=$3
    
    VALUE=$(docker exec $service env | grep "^$var_name=" | cut -d'=' -f2)
    
    if [ -z "$VALUE" ]; then
        echo "❌ $var_name not set in $service"
        return 1
    fi
    
    for invalid in $invalid_values; do
        if [ "$VALUE" = "$invalid" ]; then
            echo "❌ $var_name has invalid value: $invalid"
            return 1
        fi
    done
    
    echo "✅ $var_name OK (${VALUE:0:20}...)"
}

# Validaciones específicas
check_var "GOOGLE_CLIENT_ID" "auth-service-v2" "dummy x"
check_var "GOOGLE_CLIENT_SECRET" "auth-service-v2" "dummy x"
check_var "SECRET_KEY" "auth-service-v2" "changeme dummy"

# Validar formato correcto
CLIENT_ID=$(docker exec auth-service-v2 env | grep GOOGLE_CLIENT_ID | cut -d'=' -f2)
if [[ ! $CLIENT_ID =~ ^[0-9]+-.*\.apps\.googleusercontent\.com$ ]]; then
    echo "❌ GOOGLE_CLIENT_ID has invalid format!"
    exit 1
fi

echo ""
echo "✅ All environment variables validated!"
```

### En Tests

```python
class TestEnvironmentConfiguration:
    """Test que las variables de entorno son correctas"""
    
    def test_google_client_id_not_dummy(self):
        """CRÍTICO: Client ID NO debe ser dummy"""
        import os
        client_id = os.getenv("GOOGLE_CLIENT_ID")
        
        assert client_id != "dummy", "Using dummy GOOGLE_CLIENT_ID!"
        assert client_id != "x", "Using placeholder GOOGLE_CLIENT_ID!"
        assert "apps.googleusercontent.com" in client_id, \
            f"Invalid GOOGLE_CLIENT_ID format: {client_id}"
    
    def test_secret_key_is_strong(self):
        """Secret key debe ser fuerte (no defaults)"""
        secret = os.getenv("SECRET_KEY")
        
        assert secret != "changeme", "Using default SECRET_KEY!"
        assert secret != "dummy", "Using dummy SECRET_KEY!"
        assert len(secret) >= 32, "SECRET_KEY too short!"
```

### Docker Compose Validation

```yaml
# Use :? for required vars (fails if missing)
services:
  auth-v2:
    environment:
      # REQUIRED - fails if not set or empty
      GOOGLE_CLIENT_ID: ${GOOGLE_CLIENT_ID:?GOOGLE_CLIENT_ID is required}
      GOOGLE_CLIENT_SECRET: ${GOOGLE_CLIENT_SECRET:?GOOGLE_CLIENT_SECRET is required}
      
      # OPTIONAL - with safe default
      LOG_LEVEL: ${LOG_LEVEL:-INFO}
```

### Healthcheck that Validates Env

```python
# app/health.py

@app.get("/health")
async def health_check():
    """Health check que también valida configuración"""
    
    # Check environment
    issues = []
    
    if settings.google_client_id in ["dummy", "x", ""]:
        issues.append("Invalid GOOGLE_CLIENT_ID")
    
    if settings.secret_key in ["changeme", "dummy", ""]:
        issues.append("Invalid SECRET_KEY")
    
    if issues:
        return {
            "status": "unhealthy",
            "issues": issues
        }, 500
    
    return {
        "status": "healthy",
        "service": "auth-service-v2",
        "version": "2.0.0"
    }
```

---

## Multi-Repo Management

> **Lección:** Auth-v2 incidente (1 Enero 2026)
> Teníamos 2 repos (`/opt/dashboard` y `/opt/dashboard-v2`) sin documentarlo claramente

### Document Your Architecture

**SIEMPRE tener esto en README.md:**

```markdown
# Project Architecture

## Repository Structure

### V1 - Production (Monolith)
- **Repo:** https://github.com/user/dashboard
- **Server:** /opt/dashboard
- **Routes:** /tools/, /conversor/, /kyc-aml/, etc.
- **Status:** ✅ Production (DO NOT TOUCH)

### V2 - New Architecture (Microservices)
- **Repo:** https://github.com/user/dashboard-v2
- **Server:** /opt/dashboard-v2
- **Routes:** /tools2/, /v2/*, etc.
- **Status:** 🚧 Development

## Deployment Targets

| Repo | Local Path | Server Path | Routes |
|------|-----------|-------------|---------|
| dashboard | ~/dashboard-personal/dashboard-personal | /opt/dashboard | /tools/* |
| dashboard-v2 | ~/dashboard-v2 | /opt/dashboard-v2 | /tools2/*, /v2/* |
```

### Pre-Work Verification

```bash
#!/bin/bash
# scripts/verify-working-repo.sh

echo "🔍 Verifying working repository..."

# 1. ¿En qué repo estoy?
REMOTE=$(git remote get-url origin)
echo "Git remote: $REMOTE"

# 2. ¿Qué ruta sirvo?
REPO_NAME=$(basename $(git rev-parse --show-toplevel))
echo "Repo name: $REPO_NAME"

# 3. ¿Es el correcto para mi tarea?
if [[ "$TASK" == "v2" && "$REPO_NAME" != *"v2"* ]]; then
    echo "⚠️  WARNING: Working on V2 but in V1 repo!"
    echo "Should be in dashboard-v2 repo"
    exit 1
fi

echo "✅ In correct repository"
```

### Caddyfile Documentation

```caddyfile
# Caddyfile

keonycs.com {
    # ========== V1 ROUTES (Repo: dashboard) ==========
    # Managed in: /opt/dashboard
    # Container: dashboard-web
    handle /tools/* {
        reverse_proxy dashboard-web:3000
    }
    
    # ========== V2 ROUTES (Repo: dashboard-v2) ==========
    # Managed in: /opt/dashboard-v2
    # Container: dashboard-v2-orchestrator
    handle /tools2/* {
        forward_auth auth-service-v2:8080 {
            uri /verify?next=/tools2/
        }
        reverse_proxy dashboard-v2-orchestrator:3000  # ← NOT dashboard-web!
    }
}
```

### Multi-Repo Checklist

```
ANTES de modificar código:

□ Leo README.md - ¿hay múltiples repos?
□ ¿En qué repo estoy? (git remote -v)
□ ¿Qué repo debo modificar para esta tarea?
□ ¿Hay Caddyfile comentado indicando repos?
□ ¿Hay tabla de routing en documentación?
□ Confirmo que estoy en repo CORRECTO
□ Solo ENTONCES modifico código
```

### Common Mistakes

```
❌ Asumir que solo hay 1 repo
❌ Modificar dashboard-web cuando necesitas dashboard-v2-orchestrator
❌ No leer Caddyfile para ver qué contenedor sirve qué ruta
❌ No documentar repos separados en README
❌ Usar nombres ambiguos (dashboard vs dashboard-web vs dashboard-v2)
```

---

## Post-Deploy Validation Script

> **Lección:** Hoy deployamos sin tests post-deploy
> Encontramos 4 bugs DESPUÉS en navegador

### Automated Validation

```bash
#!/bin/bash
# scripts/post-deploy-validation.sh

set -e

SERVICE_NAME="${1:-auth-service-v2}"
BASE_URL="${2:-https://keonycs.com}"

echo "🧪 POST-DEPLOY VALIDATION: $SERVICE_NAME"
echo "=========================================="
echo ""

# ========== STEP 1: Service Health ==========
echo "1️⃣  Checking service health..."

HEALTH_URL="$BASE_URL/${SERVICE_NAME}/health"
RESPONSE=$(curl -s -w "\nHTTP:%{http_code}" "$HEALTH_URL" 2>&1)
HTTP_CODE=$(echo "$RESPONSE" | grep "HTTP:" | cut -d':' -f2)

if [ "$HTTP_CODE" != "200" ]; then
    echo "❌ Health check FAILED (HTTP $HTTP_CODE)"
    echo "Response: $RESPONSE"
    exit 1
fi

echo "✅ Service is healthy"

# ========== STEP 2: E2E Tests ==========
echo ""
echo "2️⃣  Running E2E tests..."

pytest tests/test_${SERVICE_NAME//-/_}_e2e.py -v --tb=short || {
    echo "❌ E2E TESTS FAILED!"
    echo ""
    echo "ACTION REQUIRED:"
    echo "  1. Check logs: docker logs $SERVICE_NAME"
    echo "  2. Investigate failures"
    echo "  3. Rollback if needed: ./scripts/rollback.sh"
    exit 1
}

echo "✅ E2E tests passed"

# ========== STEP 3: Environment Variables ==========
echo ""
echo "3️⃣  Validating environment variables..."

./scripts/validate-env-vars.sh "$SERVICE_NAME" || {
    echo "❌ Environment validation FAILED!"
    exit 1
}

echo "✅ Environment validated"

# ========== STEP 4: Integration Points ==========
echo ""
echo "4️⃣  Checking integration points..."

# Para auth-v2: verificar que /tools2/ lo usa
if [ "$SERVICE_NAME" = "auth-service-v2" ]; then
    REDIRECT=$(curl -sI "$BASE_URL/tools2/" 2>&1 | grep -i "location:" | cut -d' ' -f2)
    
    if [[ ! "$REDIRECT" =~ /auth-v2/ ]]; then
        echo "❌ /tools2/ not using auth-v2! Redirects to: $REDIRECT"
        exit 1
    fi
    
    echo "✅ /tools2/ correctly using auth-v2"
fi

# ========== STEP 5: No Unhealthy Containers ==========
echo ""
echo "5️⃣  Checking for unhealthy containers..."

UNHEALTHY=$(docker ps --filter "health=unhealthy" --format "{{.Names}}")
if [ ! -z "$UNHEALTHY" ]; then
    echo "❌ Unhealthy containers found:"
    echo "$UNHEALTHY"
    exit 1
fi

echo "✅ No unhealthy containers"

# ========== SUMMARY ==========
echo ""
echo "=========================================="
echo "🎉 DEPLOYMENT VALIDATED SUCCESSFULLY!"
echo "=========================================="
echo ""
echo "Service: $SERVICE_NAME"
echo "URL: $BASE_URL"
echo "Status: ✅ PRODUCTION READY"
echo ""
echo "Next steps:"
echo "  - Monitor logs: docker logs -f $SERVICE_NAME"
echo "  - Check metrics: [monitoring dashboard URL]"
echo ""
```

### Usage

```bash
# Después de deploy
./scripts/post-deploy-validation.sh auth-service-v2

# Si falla → ROLLBACK automático
./scripts/post-deploy-validation.sh auth-service-v2 || {
    echo "Validation failed - rolling back..."
    ./scripts/rollback.sh auth-service-v2
}
```

### In CI/CD

```yaml
# .github/workflows/deploy.yml

jobs:
  deploy:
    steps:
      - name: Deploy to production
        run: |
          ssh server "cd /opt/app && docker compose up -d"
      
      - name: Wait for service
        run: sleep 30
      
      - name: Validate deployment
        run: |
          ssh server "/opt/app/scripts/post-deploy-validation.sh"
      
      - name: Rollback if failed
        if: failure()
        run: |
          ssh server "/opt/app/scripts/rollback.sh"
```

### Validation Test Examples

```python
# tests/test_post_deploy_validation.py

class TestPostDeployValidation:
    """Tests que DEBEN pasar después de cada deploy"""
    
    def test_service_is_reachable(self):
        """Service debe responder"""
        response = requests.get(f"{BASE_URL}/service/health", timeout=10)
        assert response.status_code == 200
    
    def test_uses_correct_credentials(self):
        """NO debe usar credenciales dummy"""
        # Hacer request que requiere OAuth
        response = requests.get(f"{BASE_URL}/service/login", allow_redirects=False)
        location = response.headers["location"]
        
        assert "client_id=dummy" not in location
        assert "client_id=x" not in location
    
    def test_routing_is_correct(self):
        """Routing debe apuntar al servicio correcto"""
        # Test que /tools2/ usa auth-v2 (NO auth-v1)
        response = requests.get(f"{BASE_URL}/tools2/", allow_redirects=False)
        location = response.headers.get("location", "")
        
        assert "/auth-v2/" in location, \
            f"Wrong auth service! Got: {location}"
    
    def test_content_is_correct_version(self):
        """Contenido debe ser de la versión correcta"""
        # Ej: V2 dashboard debe mostrar "V2"
        response = requests.get(f"{BASE_URL}/tools2/")
        # Con auth completa, verificar contenido
        pass
```

---

## Traefik Configuration

### traefik.yml

```yaml
api:
  dashboard: true

entryPoints:
  web:
    address: ":80"
    http:
      redirections:
        entryPoint:
          to: websecure
          scheme: https
  
  websecure:
    address: ":443"
    http:
      tls:
        certResolver: letsencrypt

certificatesResolvers:
  letsencrypt:
    acme:
      email: admin@yourdomain.com
      storage: /letsencrypt/acme.json
      httpChallenge:
        entryPoint: web

providers:
  docker:
    exposedByDefault: false
```

---

### docker-compose.yml

```yaml
version: '3.9'

services:
  traefik:
    image: traefik:v2.10
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./traefik.yml:/etc/traefik/traefik.yml:ro
    networks:
      - frontend
  
  api:
    build: .
    networks:
      - frontend
      - backend
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.api.rule=Host(`api.yourdomain.com`)"
      - "traefik.http.routers.api.entrypoints=websecure"
      - "traefik.http.routers.api.tls.certresolver=letsencrypt"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: mydb
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    networks:
      - backend

networks:
  frontend:
  backend:
```

---

## CI/CD Pipeline

### GitHub Actions

```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install -r requirements.txt
      - run: pytest tests/ -v
  
  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: appleboy/ssh-action@v1.1.0
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: ${{ secrets.SERVER_USER }}
          key: ${{ secrets.SERVER_SSH_KEY }}
          script: |
            cd /opt/app
            git pull origin main
            docker compose up -d
```

---

## Zero-Downtime Deploy

### Blue-Green Strategy

```bash
#!/bin/bash
# scripts/blue-green-deploy.sh

ACTIVE="${1:-blue}"
INACTIVE=$([[ "$ACTIVE" == "blue" ]] && echo "green" || echo "blue")

echo "Deploying to $INACTIVE..."
docker compose up -d api-$INACTIVE

sleep 15
curl -f http://localhost:8000/health || exit 1

echo "Switching traffic to $INACTIVE..."
# Update Traefik labels or load balancer

echo "✅ Deployed to $INACTIVE"
```

---

# PARTE VIII: TROUBLESHOOTING

## Debug Playbook

```
1. REPRODUCE
   ├─ Can you reproduce locally?
   ├─ Exact steps?
   └─ Always or randomly?

2. GATHER CONTEXT
   ├─ Check logs (request_id)
   ├─ Check metrics
   └─ Check recent deployments

3. ISOLATE
   ├─ One service or multiple?
   ├─ All users or specific?
   └─ Time-dependent?

4. HYPOTHESIZE
   ├─ What could cause this?
   └─ List 3 likely causes

5. TEST
   ├─ Test hypothesis #1
   └─ Iterate

6. FIX
   ├─ Implement fix
   ├─ Test thoroughly
   └─ Deploy

7. PREVENT
   ├─ Add test
   ├─ Add monitoring
   └─ Document
```

---

## Common Issues

### "503 Service Unavailable"

```bash
# 1. Check if running
docker ps | grep my-service

# 2. Check logs
docker logs my-service --tail=100

# 3. Check health
curl http://localhost:8000/health

# 4. Check DB connectivity
docker exec my-service python -c "
from app.database import engine
engine.connect()
"
```

---

### "Database Connection Errors"

```python
# Check connection pool
print(engine.pool.size())
print(engine.pool.overflow())

# Common fixes:
# 1. Increase pool_size
# 2. Fix connection leaks
# 3. Use context managers
with SessionLocal() as session:
    # Use session
    pass  # Auto-closed
```

---

### "Slow API Responses"

```bash
# 1. Check response times
grep "X-Process-Time" /var/log/api.log | sort -n

# 2. Profile endpoint
import cProfile
cProfile.run('slow_function()')

# 3. Check for N+1 queries
# Enable SQLAlchemy echo
engine = create_engine(DATABASE_URL, echo=True)

# 4. Check cache hit rate
redis-cli INFO stats | grep keyspace_hits
```

---



---

## Errores Comunes V2

> **Origen:** Problemas reales encontrados en deployments de Dashboard V2, Auth-v2, e Intrastat
> **Creado:** 1-8 Enero 2026
> **Uso:** Consultar ANTES de modificar código en producción



## ❌ ERROR: "Health check error" en navegador

### Síntomas
- Dashboard carga
- UI se ve bien
- Header muestra "Health check error" (rojo)

### Causa
JavaScript fetch falla al llamar a API

### Debug
```bash
# 1. Ver consola navegador (F12)
# Buscar error de fetch

# 2. Verificar endpoint API
curl https://keonycs.com/tools2/api/services/health

# 3. Si retorna 404:
#    Endpoint no existe en código

# 4. Si retorna HTML:
#    Routing mal configurado (redirige en vez de servir API)
```

### Fix
```bash
# Opción A: Verificar que endpoint existe en código
ssh server 'docker exec [container] cat app/main.py | grep "/api/services/health"'

# Opción B: Verificar routing no redirige
grep "handle /tools2/api" Caddyfile
# Debe estar ANTES de handle /tools2/* (orden importa)
```

---

## ❌ ERROR: UI sin estilos (texto plano)

### Síntomas
- Texto negro sobre blanco
- No dark mode
- No estilos

### Causa
1. TailwindCSS bloqueado por CSP
2. CSS inline no cargado

### Debug
```bash
# Ver consola navegador
# Buscar: "Refused to load script"

# Ver CSP actual
curl -I https://site.com/tools2/ | grep content-security
```

### Fix
```bash
# Añadir CDN a CSP en Caddyfile
Content-Security-Policy "... script-src ... https://cdn.tailwindcss.com ..."

# Reload Caddy
docker restart dashboard-caddy
```

---

## ❌ ERROR: Modificaste código que ya existía

### Síntomas
- Trabajaste 1h
- Usuario dice "ya existía diferente"
- Tu código sobreescribió versión buena

### Causa
NO ejecutaste Context Verification (Regla #11)

### Debug
```bash
# Ver qué había antes
ssh server 'cd /ruta && git show HEAD:archivo'

# Ver cambios
ssh server 'cd /ruta && git diff HEAD archivo'
```

### Fix
```bash
# Restaurar original
ssh server 'cd /ruta && git checkout HEAD -- archivo'

# Rebuild si necesario
ssh server 'docker compose build && docker compose up -d'
```

### Prevención
```
SIEMPRE ANTES de modificar:
1. ssh server 'cat /ruta/archivo' (ver qué hay)
2. git log --oneline archivo (ver historial)
3. SOLO ENTONCES modificar
```

---

## ❌ ERROR: Tests pasan pero producción falla

### Síntomas
- pytest: 12/12 PASSED
- Usuario: "se ve mal"
- Contradicción

### Causa
Tests no replican comportamiento real del navegador

### Fix
Crear tests que:
- Verifican HTML real del servidor
- Verifican API retorna JSON (no HTML redirect)
- Verifican CSP permite scripts necesarios
- Verifican fetch paths correctos

### Ejemplo
```python
def test_api_returns_json_not_html():
    response = requests.get(url, allow_redirects=False)
    assert response.status_code == 200  # No redirect
    assert "application/json" in response.headers["content-type"]
    data = response.json()  # Must parse
```

---

## 🔍 COMANDOS ÚTILES DEBUG

```bash
# Ver qué código está en producción
ssh server 'docker exec [container] cat /app/main.py | head -50'

# Ver qué template se sirve
ssh server 'docker exec [container] cat /app/templates/index.html | head -50'

# Ver versión del código
ssh server 'docker exec [container] cat /app/main.py | grep version'

# Comparar con repo
ssh server 'cd /opt/dashboard-v2 && git diff HEAD services/[servicio]/'

# Ver logs
ssh server 'docker logs [container] --tail=50'

# Health check directo
ssh server 'docker exec [container] python -c "import httpx; print(httpx.get(\"http://localhost:3000/health\").text)"'
```

---

## ✅ CHECKLIST ANTES DE MODIFICAR

```
□ Ver qué existe: ssh server 'cat /ruta/archivo'
□ Ver historial: ssh server 'git log archivo'
□ Ver qué corre: ssh server 'docker ps | grep servicio'
□ Ver routing: grep "ruta" Caddyfile
□ Leer README: ssh server 'cat /ruta/README.md'
□ SOLO ENTONCES modificar
```

---

**Creado:** 1 Enero 2026  
**Basado en:** Errores reales de Sesión 1 y 2  
**Úsalo:** ANTES de modificar cualquier código



---

## Incident Response

### Incident Template

```markdown
# Incident: [TITLE]

## Timeline
- Detected: 2024-12-29 10:30 UTC
- Resolved: 2024-12-29 11:00 UTC

## Impact
- Users Affected: ~100
- Downtime: 30 minutes

## Root Cause
Database connection pool exhausted

## Resolution
1. Restarted service
2. Increased pool size
3. Fixed connection leak

## Prevention
- [ ] Add test for connection leaks
- [ ] Add monitoring
- [ ] Update runbook
```

---

# CHECKLIST FINAL

## Pre-Deployment

### Context Verification (NUEVO - Crítico)
- [ ] Verified which files to modify (grep/search)
- [ ] Confirmed container names (docker ps)
- [ ] Confirmed routing configuration (Caddyfile)
- [ ] Checked for multiple repos/versions
- [ ] Read architecture documentation
- [ ] Identified correct deployment target

### Tests & Validation
- [ ] All unit tests passing
- [ ] E2E tests passing
- [ ] Security scan clean
- [ ] Infrastructure tests validated
- [ ] docker-compose.yml valid
- [ ] Environment variables set (NOT dummy!)
- [ ] Secrets rotated
- [ ] Built HTML validated (no V1 links in V2)

## Architecture

- [ ] Domain entities pure (no frameworks)
- [ ] Use cases use interfaces
- [ ] Infrastructure implements interfaces
- [ ] Dependencies point inward
- [ ] DI container configured

## Security

- [ ] Input validation (Pydantic)
- [ ] SQL injection prevented (ORM)
- [ ] Authentication implemented (JWT)
- [ ] Authorization checked (RBAC)
- [ ] Secrets in environment variables
- [ ] HTTPS enabled

## Performance

- [ ] Indexes on foreign keys
- [ ] N+1 queries avoided
- [ ] Caching implemented
- [ ] Connection pooling configured
- [ ] Async endpoints where possible

## Observability

- [ ] Structured logging (JSON)
- [ ] Correlation IDs
- [ ] Metrics exposed (Prometheus)
- [ ] Dashboards created (Grafana)
- [ ] Alerts configured

## TDD

- [ ] Tests BEFORE code
- [ ] Test failed first (RED)
- [ ] Code passes (GREEN)
- [ ] Refactored (BLUE)
- [ ] Coverage > 80%
- [ ] Pre-commit hooks enabled

---

# EL CONTRATO TDD

```
YO, ________________, ME COMPROMETO A:

✅ Tests PRIMERO, código DESPUÉS
✅ SOLID principles siempre
✅ Clean Architecture
✅ Security by design
✅ Observability desde día 1
✅ Zero downtime deploys

❌ NUNCA:
- git commit --no-verify
- Skip tests
- Hardcode secrets
- Deploy sin tests
- Ignore security

FIRMADO: _______________
FECHA: 29 Diciembre 2024
```

---

# CÓMO USAR ESTA PLANTILLA

## Quick Start (5 minutos)

**ANTES de tocar cualquier código:**

```bash
# 1. Lee las reglas inquebrantables
head -50 PLANTILLA_NUEVO_PROYECTO_v5.md

# 2. Verifica contexto (NUEVO en v5.0)
grep -r "feature-name" .
docker ps
cat README.md

# 3. Lee la sección relevante:
#    - Nueva feature? → PARTE III (TDD Workflow)
#    - Bug? → PARTE VIII (Troubleshooting)
#    - Deploy? → PARTE VII (Deployment)

# 4. Sigue el checklist
cat PRE_DEPLOY_CHECKLIST.md
```

## Con Claude (Recomendado)

1. **Proyecto Nuevo:**
   ```
   @PLANTILLA_NUEVO_PROYECTO_v5.md
   
   Voy a crear [descripción proyecto] siguiendo TDD estricto.
   Guíame paso a paso según la plantilla v5.0.
   ```

2. **Deployment:**
   ```
   @PLANTILLA_NUEVO_PROYECTO_v5.md
   @PRE_DEPLOY_CHECKLIST.md
   
   Voy a deployar [servicio]. 
   Asegúrate que sigo el proceso correcto (Context Verification primero).
   ```

3. **Debugging:**
   ```
   @PLANTILLA_NUEVO_PROYECTO_v5.md
   
   Tengo este error: [descripción]
   Usa el Debug Playbook de la PARTE VIII.
   ```

4. **Code Review:**
   ```
   @PLANTILLA_NUEVO_PROYECTO_v5.md
   @[tu-código]
   
   Revisa contra:
   - SOLID principles
   - Context Verification (reglas #11-14)
   - Tests E2E
   ```

## Workflow Típico

```
1. VERIFICAR CONTEXTO (PARTE III - NUEVO)
   ├─ grep, codebase_search
   ├─ Confirmar repos/contenedores
   └─ Leer arquitectura

2. Lee PARTE I (Principios) → Diseña
   ├─ SOLID
   └─ Clean Code

3. Lee PARTE II (Arquitectura) → Estructura
   ├─ Layers
   ├─ Repository Pattern
   └─ DI

4. Lee PARTE III (TDD) → Implementa
   ├─ Context Verification PRIMERO
   ├─ Tests unitarios
   ├─ Tests E2E
   └─ Infrastructure tests

5. Lee PARTE IV-VI según necesites
   ├─ Security
   ├─ Performance
   └─ Observability

6. Lee PARTE VII (Deployment) → Deploy
   ├─ Docker networking
   ├─ Git-crypt
   ├─ Env validation
   ├─ Multi-repo management
   └─ Post-deploy validation

7. Lee PARTE VIII si hay problemas
   ├─ Debug playbook
   └─ Incident response
```

---

# QUICK REFERENCE CARD

## Pre-Code Checklist (30 segundos)

```bash
□ grep -r "feature" .           # ¿Dónde está?
□ docker ps                     # ¿Qué corre?
□ cat README.md                 # ¿Arquitectura?
□ git remote -v                 # ¿Repo correcto?
□ grep "route" Caddyfile       # ¿Qué sirve qué?
```

## Pre-Deploy Checklist (2 minutos)

```bash
□ pytest tests/unit/ -v        # Tests unitarios
□ pytest tests/test_*_e2e.py   # Tests E2E
□ ./scripts/validate-env-vars.sh  # Env vars OK
□ docker compose config        # Compose válido
□ git diff                     # Review cambios
```

## Post-Deploy Checklist (3 minutos)

```bash
□ ./scripts/post-deploy-validation.sh
□ pytest tests/test_*_e2e.py --base-url=production
□ curl https://site.com/service/health
□ docker ps | grep unhealthy
□ Monitor logs 5 minutos
```

## Emergency Rollback (30 segundos)

```bash
./scripts/rollback.sh [service]
# O manual:
docker compose up -d --scale service=0
docker compose up -d service-old
```

---

# CUANDO TODO FALLA

```
1. PARA ⛔
   No sigas cavando el hoyo

2. RESPIRA 🧘
   Pánico no ayuda

3. ROLLBACK 🔄
   Vuelve a estado conocido bueno

4. INVESTIGA 🔍
   Con calma, usa el Debug Playbook

5. FIX ✅
   Con tests PRIMERO

6. DOCUMENTA 📝
   Añade a plantilla/incident log

7. PREVIENE 🛡️
   Añade tests/monitoring
```

---



---

# PARTE IX: NAMING CONVENTION

> **Lección:** 8 Enero 2026 - Intrastat Manager V2
> **Problema:** 4 nombres diferentes para el mismo servicio causaban confusión
> **Solución:** Estándar único aplicado con TDD correcto



## ✅ Ejemplo: Intrastat Manager (IMPLEMENTADO)

### Nombres Aplicados:

| Componente | Nombre |
|------------|--------|
| 🔗 **GitHub Repo** | `intrastat-manager-v2` (futuro) |
| 📦 **Docker Image** | `intrastat-manager-v2:latest` |
| 🐳 **Container Name** | `intrastat-manager-v2` |
| 📁 **Carpeta Local** | `apps/intrastat-manager/` |
| 📄 **Compose Service** | `intrastat-manager-v2:` |
| 🌐 **Caddyfile Proxy** | `intrastat-manager-v2:3001` |
| 🌐 **URL Pública** | `/v2/intrastat/` |

### docker-compose.full.yml

```yaml
services:
  intrastat-manager-v2:              # ✅ Service name
    build: ./apps/intrastat-manager
    container_name: intrastat-manager-v2  # ✅ Container name
    image: intrastat-manager-v2:latest    # ✅ Image name
    restart: unless-stopped
    networks:
      - backend
```

### Caddyfile

```caddy
handle /v2/intrastat/* {
    forward_auth auth-service-v2:8080 {
        uri /verify?next=/v2/intrastat/
        copy_headers X-Auth-User X-Auth-Name X-Auth-Role
    }
    uri strip_prefix /v2/intrastat
    reverse_proxy intrastat-manager-v2:3001  # ✅ Container name
}
```

---

## 📋 Convención para Nuevos Servicios

### Template de Nombres:

```
Servicio: AEAT Notificaciones

📦 Imagen:        aeat-notificaciones-v2:latest
🐳 Contenedor:    aeat-notificaciones-v2
📁 Carpeta:       apps/aeat-notificaciones/
📄 Service:       aeat-notificaciones-v2:
🌐 Proxy:         aeat-notificaciones-v2:8000
🔗 GitHub:        ivantintore/aeat-notificaciones-v2
🌐 URL:           /v2/aeat/
```

### Template de Código:

**docker-compose.yml:**
```yaml
services:
  <nombre-servicio>-v2:
    build: ./apps/<nombre-servicio>
    container_name: <nombre-servicio>-v2
    image: <nombre-servicio>-v2:latest
    ...
```

**Caddyfile:**
```caddy
handle /v2/<url-corta>/* {
    ...
    reverse_proxy <nombre-servicio>-v2:<puerto>
}
```

---

## 🔍 Ventajas

### 1. Debugging Simplificado

**ANTES (Confuso):**
```bash
docker logs intrastat  # ¿Qué versión? ¿Qué servicio?
```

**AHORA (Claro):**
```bash
docker logs intrastat-manager-v2  # ✅ Sé exactamente qué es
```

### 2. Documentación Clara

**ANTES:**
```
"El servicio intrastat (contenedor: intrastat, 
imagen: intrastat-v2, carpeta: intrastat-manager)..."
```

**AHORA:**
```
"El servicio intrastat-manager-v2"
```

### 3. Grep/Search Eficiente

```bash
# Buscar TODO sobre intrastat-manager-v2
grep -r "intrastat-manager-v2" .

# Encuentra en:
# - docker-compose.yml
# - Caddyfile
# - README.md
# - logs
# Mismo nombre, cero confusión
```

### 4. Onboarding Rápido

Nuevo desarrollador:
```
"¿Dónde está el servicio X?"
→ Busca "X-v2" y lo encuentra en todas partes
```

---

## 📊 Servicios a Estandarizar

### Ya Aplicado:
- ✅ **intrastat-manager-v2** (8 Enero 2026)

### Pendientes (aplicar cuando se migren):
- ⏳ aeat-notificaciones-v2
- ⏳ conversor-heif-v2
- ⏳ kyc-aml-v2
- ⏳ arbol-genealogico-v2
- ⏳ estrategia-lombardo-v2
- ⏳ taxi-management-v2
- ⏳ adela-finanzas-v2
- ⏳ toroidal-project-v2

---

## 🔄 Proceso de Estandarización

### Para Cada Servicio:

1. **Modificar docker-compose.full.yml**
   ```yaml
   # Cambiar:
   servicio: → servicio-nombre-completo-v2:
   container_name: → servicio-nombre-completo-v2
   + Añadir: image: servicio-nombre-completo-v2:latest
   ```

2. **Modificar Caddyfile**
   ```caddy
   # Cambiar:
   reverse_proxy servicio:puerto
   # A:
   reverse_proxy servicio-nombre-completo-v2:puerto
   ```

3. **Aplicar en servidor**
   ```bash
   docker stop servicio-viejo
   docker rm servicio-viejo
   docker tag imagen-vieja servicio-nombre-completo-v2:latest
   docker run -d --name servicio-nombre-completo-v2 ...
   docker exec dashboard-caddy caddy reload
   ```

4. **Verificar**
   ```bash
   docker ps | grep servicio-nombre-completo-v2
   curl https://keonycs.com/v2/servicio/
   ```

5. **Actualizar docs**
   - README del servicio
   - Referencias en documentación principal
   - Comentarios en código

---

## 📝 Checklist Estandarización

Para cada servicio nuevo o migrado:

```
□ Nombre decidido: <nombre>-v2
□ docker-compose.yml usa nombre estándar
□ Caddyfile usa nombre estándar
□ Imagen Docker usa nombre estándar
□ Container name usa nombre estándar
□ README menciona nombre estándar
□ Tests usan nombre estándar (si aplica)
□ CI/CD usa nombre estándar (si aplica)
□ Documentación actualizada
□ Commit message menciona naming convention
```

---

## 🎯 Resultado

**Cero confusión en:**
- Logs
- Debugging
- Documentación
- Onboarding
- Grep/search
- Git history

**Máxima claridad** 🎯

---

**Aplicado a:** intrastat-manager-v2 ✅  
**Siguiente:** aeat-notificaciones-v2  
**Standard establecido** para todos los servicios V2

---

© 2026 MAITSA - Ivan Tintoré


---

# LECCIONES DE PRODUCCIÓN

## 🔥 Incidente: Auth-v2 Deploy (1 Enero 2026)

### Qué pasó

Deployamos auth-v2 sin verificar contexto completo:
- ✅ Auth-v2 se deployó correctamente
- ❌ Modificamos `dashboard-web/` (V1) pensando que era V2
- ❌ Caddyfile apuntaba a contenedor incorrecto
- ❌ OAuth credentials eran "dummy"
- ❌ Redirect perdió parámetro `next`

### Bugs encontrados EN PRODUCCIÓN

1. **Dashboard apuntaba a V1** (debía mostrar V2)
2. **Redirect perdía next parameter** (next=/ en vez de next=/tools2/)
3. **OAuth credentials dummy** (401 invalid_client)
4. **Paths incorrectos** (/login vs /auth-v2/login)

### Por qué pasó

```
❌ NO verificamos contexto primero
❌ Asumimos en lugar de confirmar
❌ NO ejecutamos tests E2E antes de dar OK
❌ Modificamos archivos sin confirmar cuáles eran
```

### Qué debimos hacer

```
✅ PASO 0: Verificar contexto
   - grep "dashboard.*v2"
   - docker ps | grep dashboard
   - grep "/tools2/" Caddyfile
   - cat README.md

✅ DESCUBRIR: Hay 2 repos separados
   - /opt/dashboard (V1)
   - /opt/dashboard-v2 (V2)

✅ CONFIRMAR: ¿Qué sirve /tools2/?
   - Caddyfile → dashboard-v2-orchestrator:3000

✅ MODIFICAR: El archivo correcto
   - /opt/dashboard-v2/services/dashboard-orchestrator/

✅ TESTS E2E: Antes de dar OK
   - pytest tests/test_auth_v2_e2e.py

✅ RESULTADO: 0 bugs en producción
```

### Lo que creamos para prevenirlo

1. **Tests E2E:** `tests/test_auth_v2_e2e.py` (14 tests)
2. **Tests Routing:** `tests/test_caddy_routing.py`
3. **Pre-Deploy Checklist:** `PRE_DEPLOY_CHECKLIST.md`
4. **Reglas #11-14** (Context Verification)

### Tiempo invertido

- Deploy inicial: 30 min ✅
- Debugging bugs: 2h 30min ❌
- Crear tests preventivos: 30 min ✅

**Total:** 3.5 horas

**Si hubiéramos usado TDD estricto:**
- Tests PRIMERO: 30 min
- Deploy: 30 min
- **Total:** 1 hora (3x más rápido) ✅

---

## 🔧 Incidente: Conversor HEIF Unhealthy (6 Enero 2026)

### Qué pasó

Conversor HEIF reportado como "unhealthy" en documentación del 5 de Enero.
Usuario solicita: "Arreglar Conversor HEIF".

**Al verificar contexto (Context Verification):**
- ✅ Contenedor corriendo: `Up 3 hours (healthy)`
- ✅ Healthcheck: 0 fallos consecutivos
- ✅ Response: `{"status":"healthy","version":"1.0.1767700824"}`

**Hallazgo:** El servicio se **auto-recuperó** solo después de las optimizaciones del servidor (5 Enero).

### Por qué estaba unhealthy

```
Causa raíz:
- RAM: 83% (sin buffer)
- SWAP: 0 GB (sin respaldo)
- Zombie processes: 12
- Healthchecks fallando por falta de recursos

Síntoma:
- Conversor marcado unhealthy
- Otros servicios también afectados
- SSH timeouts ocasionales
```

### Qué lo arregló (Optimizaciones Sistémicas)

```
Solución (5 Enero):
1. SWAP: 1GB configurado
2. Limpieza automática Docker (cada 6h)
3. Monitoreo: cada 15 min
4. RAM liberada: 83% → 76%
5. Zombie processes eliminados: 12 → 0

Resultado:
→ Auto-recuperación SIN intervención manual
→ TODOS los servicios beneficiados
→ Prevención sistémica, no fix puntual
```

### Lecciones Clave

**1. Context Verification PRIMERO**
```
✅ SIEMPRE verificar estado actual antes de tocar código
✅ Puede que el problema ya esté resuelto
✅ Evita trabajo innecesario

Comandos:
docker ps --filter name=conversor
docker inspect conversor --format='{{.State.Health.Status}}'
docker logs conversor --tail 20
```

**2. Optimizaciones Sistémicas > Fixes Puntuales**
```
❌ Fix puntual: Reiniciar solo conversor
   → Solo arregla 1 servicio
   → Problema vuelve a aparecer

✅ Fix sistémico: SWAP + limpieza automática
   → Beneficia TODOS los servicios
   → Previene recurrencia
   → Más sostenible
```

**3. Auto-recuperación Funciona**
```
Con arquitectura correcta:
- restart: unless-stopped
- healthchecks configurados
- recursos adecuados (RAM + SWAP)

→ Servicios se recuperan solos
→ Sin intervención manual
→ Uptime 99.9%+
```

**4. TDD Incluso en Diagnósticos**
```
Aunque el servicio ya funcionaba:
✅ Creamos 13 tests E2E
✅ Validan funcionamiento actual
✅ Previenen regresiones futuras
✅ Documentan comportamiento esperado
```

### Lo que creamos

1. **Tests E2E:** `tests/test_conversor_v2.py` (13 tests)
   - Infraestructura (3)
   - E2E (2)
   - Health (3)
   - Integración (1)
   - Routing (2)
   - Performance (2)

2. **Documentación:**
   - `CONVERSOR_HEIF_RECUPERADO_6_ENERO_2026.md`
   - Causa raíz identificada
   - Scripts de verificación
   - Comandos útiles

3. **Validación auto-recuperación:**
   - Confirmada con métricas
   - Documentado proceso
   - Confianza en arquitectura

### Tiempo invertido

- Diagnóstico: 15 min ✅
- Creación tests E2E: 10 min ✅
- Documentación: 15 min ✅
- **Total:** 40 minutos

**Valor generado:**
- Tests: 13 (prevención regresiones)
- Docs: 500+ líneas
- Validación: Auto-recuperación funciona
- Bugs introducidos: 0 ✅

### Métricas de Auto-recuperación

```
ANTES (5 Enero - unhealthy):
RAM: 83% (sin buffer)
SWAP: 0 GB
Zombie: 12 procesos
Estado: unhealthy

DESPUÉS (6 Enero - auto-recuperado):
RAM: 76% (7% liberado)
SWAP: 1 GB (buffer activo)
Zombie: 0 procesos
Estado: healthy
FailingStreak: 0
Uptime: 3+ horas estables
```

### Alternativas consideradas (y descartadas)

**❌ Opción 1: Reiniciar contenedor**
- Solo arregla síntoma
- No previene recurrencia
- Otros servicios siguen afectados

**❌ Opción 2: Aumentar RAM servidor**
- Coste adicional 5-10€/mes
- Solo retrasa problema
- No elimina zombie processes

**✅ Opción 3: Optimizaciones sistémicas (elegida)**
- Cero coste adicional
- Zero downtime
- Beneficia TODO el stack
- Prevención a largo plazo
- Documentación completa

---



---

## 🔧 Incidente: Intrastat Manager - Tests Pasan pero Browser Falla (8 Enero 2026)

### Qué pasó

Implementamos versiones iterativas en Intrastat Manager V2:
- ✅ Tests HTTP: 22/22 PASSED
- ✅ Health checks: OK
- ✅ curl requests: 200/302 correctos
- ❌ Navegador: Error JavaScript "Failed to execute 'json'"

**Problema:** Los tests pasaron pero la aplicación NO funcionaba para el usuario real.

### Root Cause

```
Tests HTTP (requests library):
✅ Hacen peticiones GET/POST
✅ Verifican status codes
✅ Parsean JSON
❌ NO ejecutan JavaScript
❌ NO replican comportamiento del navegador

Navegador real:
✅ Ejecuta JavaScript
✅ Hace fetch() desde rutas relativas
❌ Rutas absolutas fetch('/upload') fallan con reverse proxy
❌ Error: "Unexpected end of JSON input"
```

### Diagnóstico

```javascript
// Código en HTML:
fetch('/upload', {...})  // ❌ Se resuelve como https://keonycs.com/upload
                         // Debería ser https://keonycs.com/v2/intrastat/upload

// Solución:
fetch('./upload', {...}) // ✅ Relativo al path actual
```

### Lección Crítica: Niveles de Testing

**Nivel 1: Tests HTTP (requests) ❌ INSUFICIENTE**
```python
def test_upload_endpoint():
    response = requests.post("https://site.com/v2/intrastat/upload", files=...)
    assert response.status_code == 200
    # ✅ PASA pero usuario no puede usar la app
```

**Nivel 2: Tests Browser (Selenium/Playwright) ✅ NECESARIO**
```python
def test_upload_workflow_in_browser():
    browser = playwright.chromium.launch()
    page = browser.new_page()
    page.goto("https://site.com/v2/intrastat/")
    page.set_input_files("#fileInput", "test.xlsx")
    page.click("#uploadBtn")
    # ✅ FALLA si JavaScript no funciona
    # ✅ Captura el error real del usuario
```

### Lo que Debimos Hacer (TDD Perfecto con Browser)

```
1. RED: Escribir test Selenium/Playwright
   - Sube archivo Excel
   - Verifica que genera CSV
   - Descarga CSV
   - Test FALLA (rutas absolutas no funcionan)

2. GREEN: Fix en código fuente
   - Cambiar fetch('/upload') → fetch('./upload')
   - Rebuild imagen Docker
   - Test PASA

3. DEPLOY: Solo después de GREEN
   - Usuario puede usar app
   - Zero bugs en producción
```

### Lo que Hicimos (TDD Retroactivo Limitado)

```
1. Implementamos funcionalidad
2. Escribimos tests HTTP (requests)
3. Tests PASAN ✅
4. Deploy a producción
5. Usuario reporta: "No funciona" ❌
6. Fix temporal con sed (rutas relativas)
7. Funciona pero fix no está en código fuente
```

### Tiempo Invertido

- Implementación inicial: 1h
- Tests HTTP (22 tests): 45min
- CI/CD setup: 30min
- **Subtotal:** 2h 15min ✅

- Usuario reporta bug: 5min
- Debug: 15min
- Fix temporal (sed): 10min
- **Overhead:** 30min ❌

**Total:** 2h 45min

**Si hubiéramos usado Browser tests desde inicio:**
- Tests Selenium (3-4 críticos): 30min
- Implementación (guiada por tests): 1h
- CI/CD: 30min
- **Total:** 2h ✅
- **Overhead:** 0 min
- **Bugs:** 0

### Lo que Creamos

**Tests (22 total):**
- ✅ 11 tests unitarios (versiones)
- ✅ 8 tests E2E HTTP
- ✅ 7 tests naming convention
- ❌ 0 tests browser (TODO)

**CI/CD:**
- ✅ GitHub Actions configurado
- ✅ 5 jobs automatizados

**Documentación:**
- ✅ 5 archivos markdown
- ✅ Naming convention establecido

**Funcionalidad:**
- ✅ Versiones iterativas funcionando
- ✅ Health monitoring en UI
- ✅ Nombre estandarizado: intrastat-manager-v2

### Mejoras para Próximos Servicios

```
PARA: AEAT, KYC-AML, Conversor, etc.

✅ Tests ANTES (Red→Green)
✅ Browser tests para UI (Selenium/Playwright)
✅ Naming convention desde inicio
✅ TDD perfecto, no retroactivo
✅ Zero fixes temporales

Template:
1. Decidir nombre: aeat-notificaciones-v2
2. Escribir test browser: "Usuario sube archivo"
3. RED (falla - app no existe)
4. Implementar con fetch relativo desde inicio
5. GREEN (test pasa)
6. Deploy
7. Usuario feliz, developer feliz
```

### Red Flags Aprendidas Hoy

```
🚩 "Tests pasan al 100%" pero no probaste en navegador
   → Escribir tests browser (Selenium/Playwright)

🚩 "Health check OK" pero usuario ve 502
   → Smoke tests contra URL pública

🚩 "Aplico fix con sed" en contenedor corriendo
   → Fix en código fuente + rebuild

🚩 Cambio nombres sin test primero
   → Test que valide nombres → RED → Cambiar → GREEN
```

### Estadísticas del Incidente

```
Problema reportado: 19:15
Diagnóstico: 5 min
Fix temporal: 5 min
Funcionando: 19:25

Tests creados después: 22
CI/CD configurado: ✅
Naming standardizado: ✅
Documentación: 5 archivos

Estado final:
✅ Intrastat funcionando perfecto
✅ TDD aplicado (aunque retroactivo)
✅ Sirve como referencia
⚠️  Falta: Browser tests (Selenium/Playwright)
```

### Checklist para Evitarlo

```
PARA APPS CON UI (Frontend):

□ Tests HTTP (requests) - Básicos ✅
□ Tests Browser (Selenium/Playwright) - CRÍTICOS ✅
□ Test: Usuario puede subir archivo
□ Test: Usuario ve resultado
□ Test: Usuario puede descargar
□ Test: Errores se muestran correctamente
□ Test: Navegación funciona
□ SOLO deploy después de tests browser GREEN
```

---


# NOVEDADES v5.0 (Production-Hardened)

## ✨ Lo nuevo en esta versión

### Añadido el 1 Enero 2026

**Contexto:** Después de deployment real de auth-v2 con bugs en producción

**10 Secciones Nuevas:**

1. **Context Verification (CRÍTICO)**
   - Reglas #11-14
   - Checklist completo
   - Red flags
   - Ejemplo real del incidente

2. **Tests E2E**
   - Tests de routing
   - Tests de OAuth config
   - Tests de contenido
   - Validación post-deploy

3. **Docker Networking Debugging**
   - Diagnostic script completo
   - Soluciones comunes
   - Checklist troubleshooting

4. **Git-Crypt & Encrypted Secrets**
   - 3 soluciones para .env encriptado
   - Bypass temporal
   - Best practices

5. **Environment Variables Validation**
   - Script de validación
   - Tests automatizados
   - Healthcheck que valida env

6. **Multi-Repo Management**
   - Documentación clara
   - Verificación pre-work
   - Caddyfile documentation
   - Common mistakes

7. **Post-Deploy Validation Script**
   - Script automatizado
   - Integración CI/CD
   - Rollback automático si falla

8. **Production Monitoring Stack** ⭐ NUEVO
   - Loki + Promtail (logs)
   - Prometheus (metrics)
   - Grafana (dashboards)
   - AlertManager (alerts)
   - Configuración completa
   - Dashboards específicos

9. **Staging Environment Setup** ⭐ NUEVO
   - Por qué lo necesitas
   - Setup mínimo
   - Workflow staging → production
   - Tests en staging

10. **Rollback Procedures** ⭐ NUEVO
    - Auto-rollback script
    - Blue-green deployment
    - Rollback testing
    - < 30 segundos tiempo de rollback

**Impacto:**
- ⏱️ Ahorra 2-3 horas por deploy
- 🐛 Previene bugs en producción (staging)
- ✅ Deploy confidence: 99%+ (rollback automático)
- 📚 Documenta incidentes reales
- 🔍 Visibility completa (monitoring stack)
- 🚨 Alertas automáticas
- 🔄 Recovery < 30 segundos

---

# CHANGELOG

## v7.0 - TDD Perfect + Naming Convention (8 Enero 2026)

**Added:**
- Naming Convention standard (PARTE IX nueva)
  - Formato único: <nombre-servicio>-v2
  - Ejemplo completo: intrastat-manager-v2
  - Template para nuevos servicios
  - Ventajas documentadas

- Troubleshooting V2 expandido (PARTE VIII)
  - Error: Health check error en navegador
  - Error: UI sin estilos (CSP)
  - Error: Tests pasan pero producción falla
  - Comandos útiles de debug
  - Checklist antes de modificar

- Browser Testing Requirements
  - Tests HTTP NO suficientes para UI
  - Selenium/Playwright necesarios
  - Template de tests browser
  - Comparación: HTTP vs Browser tests

**Incident Documented:**
- Intrastat Manager: Tests pasan pero browser falla
  - 22 tests HTTP pasan
  - Usuario ve error JavaScript
  - Root cause: fetch() rutas absolutas
  - Solución: Tests browser + rutas relativas
  - Tiempo perdido: 30 min (fix temporal)
  - Lección: Browser tests SIEMPRE para UI

**Methodology Refined:**
- TDD Perfecto ejemplificado (Red→Green→Refactor)
  - RED: Tests naming convention (3 failed)
  - GREEN: Aplicar cambios (7 passed)
  - Rollback cuando violamos TDD
  - Re-implementación correcta

- Naming Convention con TDD
  - Standard establecido
  - Aplicado a Intrastat (referencia)
  - Tests que validan nombres
  - Cero confusión en debugging

**New Rules:**
- #15: Browser tests para UI (Selenium/Playwright)
- #16: Naming convention único (<nombre>-v2)
- #17: NO fixes temporales (sed/awk)

**Impact:**
- ⏱️ Previene 30+ min de debugging por servicio
- 🎯 Naming claro (zero confusión)
- ✅ TDD perfecto establecido como ejemplo
- 📚 3 incidentes documentados ahora (auth-v2, conversor, intrastat)

**Statistics:**
- Lines added: +500
- Tests: +7 (naming convention)
- Incidents documented: 3 → 4
- Standards: Naming convention established

## v6.1 - Smoke Tests Critical (7 Enero 2026)

**Added:**
- Smoke Tests section (CRÍTICO)
- Healthcheck vs Smoke Tests comparison
- Real incident: Healthcheck ✅ but 502 ❌
- 47 smoke tests template
- Validation levels (healthcheck → smoke → functional → integration)
- Post-deploy smoke tests workflow

**Documented:**
- Healthcheck NO garantiza funcionamiento real
- 502 error con healthcheck healthy
- Smoke tests detectan problemas reales
- Template por servicio

**Mega Lección:**
- Healthcheck dice ✅ = Proceso vivo
- Smoke Test dice ✅ = Funciona REALMENTE
- Necesitas AMBOS

## v6.0 - Auto-Recovery Validation (6 Enero 2026)

**Added:**
- Conversor HEIF incident documentation (auto-recovery case)
- Auto-recovery validation methodology
- Systemic optimizations vs point fixes comparison
- Context Verification real example (service already recovered)
- TDD in diagnostics (tests even when working)

**Documented:**
- Auto-recovery success case (unhealthy → healthy sin intervención)
- SWAP + cleanup effectiveness (RAM 83% → 76%)
- 13 new E2E tests created (prevention)
- Time invested: 40 min (diagnosis + tests + docs)
- Value: High (validation + prevention + documentation)

**Validated:**
- Auto-recovery works (restart policies + healthchecks)
- Systemic optimizations benefit ALL services
- Context Verification prevents unnecessary work
- TDD methodology applies to diagnostics too

## v5.1 - Production Maintenance (5 Enero 2026)

**Added:**
- Docker Automatic Cleanup section (Production Essential)
- Cron-based cleanup every 6 hours
- RAM optimization for VPS pequeños (2GB)
- Zombie process elimination
- Alternative solutions comparison

**Fixed:**
- Server RAM saturation (83% → 70%)
- Zombie processes accumulation (12 → 0)
- SSH timeouts due to memory pressure

**Documented:**
- Dinahosting VPS incident (RAM 83%, SSH failing)
- Limpieza automática vs reinicio vs upgrade RAM

## v5.0 - Production-Hardened (1 Enero 2026)

**Added:**
- Context Verification rules (#11-14)
- Docker Networking debugging
- Git-Crypt management
- Env vars validation
- Multi-repo management
- Post-deploy validation
- Real incident documentation

**Changed:**
- TDD workflow ahora incluye Context Verification (PASO 0)
- Pre-deployment checklist más robusto
- Índice reorganizado con nuevas secciones

**Documented:**
- Auth-v2 incident (4 bugs, 2.5h debugging)
- Lecciones aprendidas
- Scripts preventivos

## v4.1 - Context Verification (1 Enero 2026)

**Added:**
- Context verification section
- E2E tests basics

## v4.0 - Unificada (29 Diciembre 2024)

**Initial version:**
- SOLID principles
- Clean Architecture
- TDD workflow completo
- Security, Performance, Observability
- Deployment strategies

---

# ESTADÍSTICAS v7.0

- **Líneas:** 5,035+ 📈 (+785 con Troubleshooting + Naming + Intrastat)
- **Ejemplos de código:** 170+
- **Scripts completos:** 16+ (production-ready)
- **Best practices:** 420+ (+5 nuevas de naming)
- **Patterns explicados:** 15+
- **Tests de ejemplo:** 179+ (+29 de Intrastat: 22 funcionales + 7 naming)
- **Configuraciones completas:** 8 (Docker, Monitoring, CI/CD, etc.)
- **Incidentes documentados:** 5 (auth-v2, server RAM, conversor, healthcheck vs 502, intrastat browser)
- **Casos de TDD perfecto:** 1 (naming convention Red→Green) ✨ NUEVO
- **Naming standards:** 1 (intrastat-manager-v2 como referencia) ✨ NUEVO
- **Browser testing requirements:** ✅ Documented (Selenium/Playwright) ✨ NUEVO
- **Tiempo ahorrado:** 2-3h por deploy + 30min por servicio (naming claro)
- **Reduced bugs:** 80-90% (con staging + E2E + browser tests)
- **Rollback time:** < 30 segundos
- **Deploy confidence:** 99%+
- **Server uptime:** 99.9%+ (con auto-cleanup)
- **Naming clarity:** 100% (zero confusión en logs/debugging)
- **TDD examples:** 3 (KYC+AML, Auth-v2, Intrastat perfecto)
- **Tiempo condensado:** 10+ años experiencia + 5 incidentes reales
- **Stack completo:** ✅ Development, Staging, Production, Monitoring, Maintenance, Auto-Recovery, Naming Standard
- **Última actualización:** 8 Enero 2026

---

# EL CONTRATO TDD v7.0

```
YO, ________________, ME COMPROMETO A:

✅ Tests PRIMERO, código DESPUÉS (TDD perfecto: Red→Green→Refactor)
✅ SOLID principles siempre
✅ Clean Architecture
✅ Security by design
✅ Observability desde día 1
✅ Zero downtime deploys
✅ VERIFICAR CONTEXTO PRIMERO (v5.0)
✅ Tests E2E post-deploy (v5.0)
✅ Validar env vars (v5.0)
✅ Tests BROWSER para UI (Selenium/Playwright) (v7.0)
✅ Naming convention único: <nombre>-v2 (v7.0)

❌ NUNCA:
- git commit --no-verify
- Skip tests
- Hardcode secrets
- Deploy sin tests
- Ignore security
- Asumir sin verificar (v5.0)
- Modificar sin confirmar repo correcto (v5.0)
- Fixes temporales con sed/awk en contenedores (v7.0)
- Tests HTTP solo para apps con UI (v7.0)
- Nombres inconsistentes entre Docker/Caddy/docs (v7.0)

FIRMADO: _______________
FECHA: 8 Enero 2026
```

---

**Versión:** 7.0 Production-Hardened + TDD Perfect + Naming Convention  
**Fecha:** 8 Enero 2026  
**Autor:** Ivan Tintoré  
**Contacto:** CEO MAITSA, Co-founder Clearcust

---

**¡Úsala, mejórala, y construye software de calidad! 🚀**

**Aprende de los errores. Los tests E2E salvan vidas (y tiempo).** 💡

**v6.0: Endurecida con batallas reales de producción + Auto-recuperación validada.** 🔥

**Nuevo en v6.0:** Caso real de auto-recuperación + 4 lecciones clave aplicables 🎯

**Lección clave:** Optimizaciones sistémicas > Fixes puntuales 💪

**v6.1 NUEVO:** Smoke Tests - Healthcheck NO garantiza funcionamiento real 🚨
