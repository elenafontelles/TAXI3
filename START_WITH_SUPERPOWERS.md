# 🚀 START WITH SUPERPOWERS - GUÍA DE INICIO

**Proyecto:** TAXI API  
**Fecha:** 27 Enero 2026  
**Plugin:** Superpowers Skills instalado ✅

---

## 📋 PRE-REQUISITOS

✅ Superpowers plugin instalado  
✅ TAXI_API_SPEC.md completo (5,510 líneas)  
✅ PLANTILLA_NUEVO_PROYECTO_v7.md disponible  
✅ Git repo inicializado (https://github.com/ivantintore/TAXI2)  

---

## 🎬 PASO 1: Comando Inicial en Claude Code

**Copia esto EXACTAMENTE en el chat de Cursor:**

```
@TAXI_API_SPEC.md @PLANTILLA_NUEVO_PROYECTO_v7.md @PLANTILLA_VERIFICACION.md 

🚀 INICIO DE PROYECTO TAXI API CON SUPERPOWERS

CONTEXTO DEL PROYECTO:
Vamos a implementar un sistema de gestión y facturación para 3 taxis que consolida datos de múltiples plataformas (Uber, FreeNow, Prima).

ESPECIFICACIÓN COMPLETA:
- TAXI_API_SPEC.md: 5,510 líneas de spec production-ready
- Arquitectura: Clean Architecture estricta
- Stack: PostgreSQL + FastAPI + Celery + Docker
- Testing: TDD obligatorio (RED→GREEN→REFACTOR)
- Deployment: Docker + CI/CD + Zero-downtime

REGLAS INQUEBRANTABLES (de PLANTILLA v7.0):
1. Tests PRIMERO, código DESPUÉS (sin excepciones)
2. SOLID principles siempre
3. Clean Architecture (Domain → Application → Infrastructure)
4. Security by design
5. Observability desde día 1
6. NUNCA código sin tests

WORKFLOW SUPERPOWERS A SEGUIR:
✅ Fase 1: Brainstorming (SALTAR - ya tenemos TAXI_API_SPEC.md completo)
✅ Fase 2: Git Worktrees (crear branch feature/initial-setup)
✅ Fase 3: Writing Plans (descomponer en tareas 2-5 min)
✅ Fase 4: Execution (TDD estricto con subagents)
✅ Fase 5: Test-Driven Development (RED→GREEN→REFACTOR obligatorio)
✅ Fase 6: Code Review (revisión continua)
✅ Fase 7: Finishing (merge cuando todo pase tests)

PRIORIDAD DE IMPLEMENTACIÓN:
1. Estructura de carpetas (Sección 9.2 del spec)
2. Docker setup (Dockerfile, docker-compose.yml de Sección 9.1)
3. Domain layer (Trip, Driver, Vehicle entities) con TDD
4. Infrastructure layer (SQLAlchemy models + Repositories)
5. Database setup (PostgreSQL + Alembic migrations)
6. API layer (Health endpoint + GET /trips)
7. Tests: Unit (domain) + Integration (repository) + E2E (API)

PREGUNTA INICIAL:
¿Has leído y comprendido TAXI_API_SPEC.md? 
¿Estás listo para activar Superpowers workflow empezando con Fase 2 (Git Worktrees)?
```

---

## 🔍 PASO 2: Superpowers Activará Automáticamente

### **Fase 2: Git Worktrees** (usando-git-worktrees skill)

Superpowers ejecutará:

```bash
# 1. Crear worktree aislado
git worktree add ../taxi-api-dev -b feature/initial-setup

# 2. Cambiar a ese directorio
cd ../taxi-api-dev

# 3. Verificar baseline (si hay tests)
# Como es proyecto nuevo, creará estructura base primero
```

**Respuesta esperada de Claude:**
```
✅ Git worktree created: ../taxi-api-dev
✅ Branch: feature/initial-setup
✅ Baseline verified (clean slate)

Proceeding to Phase 3: Writing Plans
```

---

### **Fase 3: Writing Plans** (writing-plans skill)

Superpowers generará un plan detallado:

```markdown
## 📋 IMPLEMENTATION PLAN

### Epic 1: Project Foundation (Estimate: 45 min)

#### Task 1.1: Create directory structure [2 min]
**Files to create:**
- src/domain/entities/
- src/domain/repositories/
- src/domain/value_objects/
- src/application/use_cases/
- src/infrastructure/database/models/
- src/infrastructure/database/repositories/
- src/api/routes/
- tests/unit/domain/
- tests/integration/
- tests/e2e/

**Verification:**
```bash
tree src/
# Should match structure from TAXI_API_SPEC.md Section 9.2
```

**Success criteria:**
- [ ] All directories exist
- [ ] __init__.py in each Python package

---

#### Task 1.2: Setup requirements.txt [3 min]
**Files to create:**
- requirements.txt
- requirements-dev.txt

**Content (based on spec):**
```txt
# requirements.txt
fastapi==0.109.0
uvicorn[standard]==0.27.0
sqlalchemy==2.0.25
alembic==1.13.1
psycopg2-binary==2.9.9
celery==5.3.6
redis==5.0.1
pydantic==2.5.3
pydantic-settings==2.1.0
python-multipart==0.0.6
```

**Verification:**
```bash
pip install -r requirements.txt
python -c "import fastapi; print(fastapi.__version__)"
```

**Success criteria:**
- [ ] All dependencies install without errors
- [ ] Imports work

---

(Continúa desglosando TODO el proyecto en tareas de 2-5 min)
```

---

### **Fase 4: Execution** (TDD obligatorio)

Para **CADA tarea**, Superpowers hará:

```
┌─────────────────────────────────────────────────────┐
│ Task 2.1: Implement Trip Entity                     │
├─────────────────────────────────────────────────────┤
│                                                      │
│ 🔴 STEP 1: RED (Write failing test)                │
│    File: tests/unit/domain/test_trip_entity.py     │
│    Verify: pytest MUST FAIL                         │
│                                                      │
│ 🟢 STEP 2: GREEN (Minimal implementation)          │
│    File: src/domain/entities/trip.py               │
│    Verify: pytest MUST PASS                         │
│                                                      │
│ 🔵 STEP 3: REFACTOR (Improve code)                 │
│    Clean code, SOLID, docstrings                    │
│    Verify: pytest STILL PASSES                      │
│                                                      │
│ ✅ STEP 4: COMMIT                                   │
│    git add . && git commit -m "Add Trip entity"     │
│                                                      │
└─────────────────────────────────────────────────────┘

Anti-pattern detection:
❌ If code written before test → DELETE CODE + start over
❌ If test always passes → REWRITE TEST
❌ If no verification → BLOCK PROGRESS
```

---

### **Fase 6: Code Review** (después de cada Epic)

```
🔍 CODE REVIEW: Epic 1 Complete

✅ PASS (Continue):
- All 5 tasks completed
- 12 tests passing (100% coverage in domain layer)
- Clean Architecture respected
- SOLID principles followed
- No security issues

⚠️ WARNINGS (Fix recommended):
- trip.py line 45: Consider extracting validation to Value Object
- Suggestion: Create Money value object for amount + currency

❌ CRITICAL (BLOCKING - must fix):
- None

Score: 9.5/10

Options:
1. Continue to Epic 2 (Repository Pattern)
2. Address warnings first
3. Review code manually

Your choice?
```

---

## 📖 PASO 3: Durante la Ejecución

### **Lo que verás en el chat:**

```
[Superpowers - Phase 3]
Creating implementation plan from TAXI_API_SPEC.md...

Plan created: 8 Epics, 42 Tasks
Estimated time: 4-6 hours
Test coverage target: >80%

Epic 1: Project Foundation (8 tasks)
Epic 2: Domain Layer (12 tasks)
Epic 3: Infrastructure Layer (10 tasks)
Epic 4: API Layer (6 tasks)
Epic 5: Docker Setup (4 tasks)
Epic 6: CI/CD (2 tasks)

Starting execution with TDD...
```

---

```
[Task 1.1] Create directory structure
✅ Directories created (verified)

[Task 1.2] Setup requirements.txt
✅ Dependencies defined (verified)

[Task 2.1 - RED] Write test_trip_entity.py
📝 Test written
🔴 Running pytest... FAILED ✅ (expected)

[Task 2.1 - GREEN] Implement Trip entity
💻 Code written
🟢 Running pytest... PASSED ✅

[Task 2.1 - REFACTOR] Clean code improvements
♻️ Refactored
🟢 Running pytest... PASSED ✅

[Task 2.1 - COMMIT] 
✅ git commit -m "Add Trip entity with tests"

Progress: 2/42 tasks (5%)
```

---

## 🛡️ PASO 4: Anti-Patterns que Superpowers Previene

### **Scenario 1: Código sin tests**

```
🤖 Claude intenta:
"Let me create the Trip entity..."
[Writes code in src/domain/entities/trip.py]

🚫 Superpowers skill bloquea:
"❌ VIOLATION: Code written before test
 
Action: Deleting code
Reason: TDD requires test-first approach

Please write the test in tests/unit/domain/test_trip_entity.py first"

[Deletes the code]
```

---

### **Scenario 2: Test que siempre pasa**

```
🤖 Claude escribe test:
def test_trip_creation():
    assert True  # ❌ Siempre pasa

🚫 Superpowers detecta:
"❌ ANTI-PATTERN: Trivial test
 
This test always passes and doesn't verify behavior.

Rewrite to test actual Trip functionality:
- Create Trip with valid data
- Verify properties
- Test business logic"
```

---

### **Scenario 3: Sin verificación**

```
🤖 Claude dice:
"I've implemented the repository"

🚫 Superpowers exige:
"❌ EVIDENCE REQUIRED

You must verify the implementation works:
1. Run: pytest tests/integration/test_trip_repository.py
2. Show output
3. Confirm tests pass

No claims without evidence."
```

---

## 📊 PASO 5: Tracking de Progreso

Superpowers mantiene un archivo de progreso:

```markdown
# .superpowers/progress.md

## Implementation Progress

Last updated: 2026-01-27 11:30:00

### Epic 1: Project Foundation ✅ COMPLETE
- [x] Task 1.1: Directory structure (2 min) ✅
- [x] Task 1.2: Requirements (3 min) ✅
- [x] Task 1.3: Docker files (5 min) ✅
...

### Epic 2: Domain Layer 🔄 IN PROGRESS (40%)
- [x] Task 2.1: Trip entity + tests ✅
- [x] Task 2.2: Driver entity + tests ✅
- [ ] Task 2.3: Vehicle entity + tests
- [ ] Task 2.4: Money value object + tests
...

### Statistics:
- Tasks completed: 8/42 (19%)
- Tests passing: 24
- Coverage: 87%
- Time elapsed: 1.2 hours
- Estimated remaining: 3.8 hours
```

---

## 🎯 PASO 6: Cuando Todo Esté Listo

```
[Superpowers - Phase 7: Finishing]

✅ ALL TASKS COMPLETE

Summary:
- 42/42 tasks completed
- 86 tests passing (0 failures)
- Coverage: 94.2%
- Code review score: 9.8/10
- 0 critical issues

Repository state:
- Branch: feature/initial-setup
- Commits: 42 (one per task)
- All tests passing
- Pre-commit hooks verified

Options:
1. 🔀 Merge to main (recommended)
2. 📝 Create Pull Request for review
3. 🔄 Continue development (more features)
4. 🗑️ Discard branch (not recommended)

What would you like to do?
```

---

## 🚀 **AHORA SÍ: COMANDO INICIAL PARA SUPERPOWERS**

Copia esto en Cursor/Claude Code (asegúrate de mencionar los 3 archivos con @):

```
@TAXI_API_SPEC.md @PLANTILLA_NUEVO_PROYECTO_v7.md @PLANTILLA_VERIFICACION.md 

🚀 INICIAR IMPLEMENTACIÓN TAXI API CON SUPERPOWERS

PROYECTO: Sistema centralizado de facturación para 3 taxis
ESPECIFICACIÓN: 5,510 líneas production-ready (93% cobertura plantilla v7.0)

ARQUITECTURA:
- Clean Architecture (Domain → Application → Infrastructure → API)
- PostgreSQL 15 + FastAPI + Celery + Redis + Docker
- TDD ESTRICTO con coverage >80%
- CI/CD con GitHub Actions
- Zero-downtime deploys

DOCUMENTOS QUE DEBES LEER:
1. TAXI_API_SPEC.md - Especificación técnica completa
   - Sección 4: Modelo de datos (8 tablas)
   - Sección 9: Estructura del proyecto + Docker + Persistencia
   - Sección 11-13: CI/CD, Testing, Operations

2. PLANTILLA_NUEVO_PROYECTO_v7.md - Reglas inquebrantables
   - SOLID principles
   - Repository Pattern
   - TDD workflow

3. PLANTILLA_VERIFICACION.md - Gaps analysis
   - Qué sí tenemos (93%)
   - Qué falta (7% postponed)

WORKFLOW SUPERPOWERS:
✅ Fase 1 (Brainstorming): SALTAR - spec ya completa
✅ Fase 2 (Git Worktrees): Crear branch feature/initial-setup
✅ Fase 3 (Writing Plans): Descomponer en tareas 2-5 min
✅ Fase 4 (Execution): TDD estricto con subagents
✅ Fase 5 (TDD Enforcement): RED→GREEN→REFACTOR obligatorio
✅ Fase 6 (Code Review): Revisión cada 5 tareas
✅ Fase 7 (Finishing): Merge cuando tests pasen

PRIORIDAD TAREAS (primeras 2 horas):
1. Estructura de carpetas completa (como Sección 9.2)
2. requirements.txt + requirements-dev.txt
3. Dockerfile + docker-compose.yml (multi-stage de Sección 9.1)
4. Domain entities con TDD:
   - Trip entity (CORE) + tests
   - Driver entity + tests
   - Vehicle entity + tests
   - Money value object + tests
5. Infrastructure:
   - SQLAlchemy models (TripModel, DriverModel, VehicleModel)
   - Repository Pattern (interfaces + implementations)
   - Database connection (Sección 9.3.1)
6. First API endpoint: GET /health (con checks de Sección 13.5.3)
7. Pre-commit hooks (.pre-commit-config.yaml de Sección 11.1)

OBJETIVO SESIÓN 1:
✅ Estructura completa del proyecto
✅ Domain layer con tests (100% coverage)
✅ PostgreSQL corriendo en Docker
✅ Health endpoint funcionando
✅ 30-40 tests pasando

IMPORTANTE:
- Si intentas escribir código SIN test primero → skill TDD te bloqueará
- Cada tarea debe tener verificación ejecutable
- No avanzar sin evidence (tests pasando)

PREGUNTA:
¿Has leído toda la especificación? ¿Entiendes la arquitectura Clean? ¿Activamos Fase 2 (Git Worktrees)?
```

---

## ✅ CHECKLIST PRE-INICIO

Antes de ejecutar el comando, verifica:

- [ ] Estás en `/Users/ivantintore/TAXI_API/` directory
- [ ] Git repo está limpio (`git status` → clean)
- [ ] Superpowers plugin está instalado en Cursor
- [ ] Tienes los 3 archivos abiertos (@TAXI_API_SPEC.md, @PLANTILLA, @VERIFICACION)

---

## 🎯 RESPUESTAS ESPERADAS DE SUPERPOWERS

### **Respuesta 1: Comprensión del Proyecto**

```
✅ Specification read and understood.

Project summary:
- 3 taxis (2 Iván, 1 Elena)
- Multi-platform sync (Uber API, FreeNow CSV, Prima CSV)
- 8 database tables (trips as CORE table)
- Clean Architecture with Repository Pattern
- TDD mandatory (RED→GREEN→REFACTOR)

Architecture layers verified:
✓ Domain: Entities + Repository interfaces (no DB dependencies)
✓ Application: Use cases (orchestration)
✓ Infrastructure: SQLAlchemy + Connectors
✓ API: FastAPI endpoints

Activating Phase 2: Git Worktrees
```

---

### **Respuesta 2: Plan de Tareas**

```
📋 PLAN CREATED

8 Epics | 42 Tasks | Est. 4-6 hours

Epic 1: Foundation (8 tasks, 45 min)
  ├─ 1.1 Directory structure [2 min]
  ├─ 1.2 Dependencies [3 min]
  ├─ 1.3 Docker setup [5 min]
  └─ ... 5 more tasks

Epic 2: Domain Layer TDD (12 tasks, 1.5 hours)
  ├─ 2.1 Trip entity + tests [5 min]
  ├─ 2.2 Driver entity + tests [4 min]
  └─ ... 10 more tasks

...

Ready to execute?
Options:
1. Start full execution (recommended)
2. Execute Epic 1 only (checkpoint after foundation)
3. Review plan first

Your choice?
```

**Tu respuesta**: Elige `1` para ejecución completa o `2` para ir por fases.

---

## 🎬 ACCIÓN AHORA

**Copia el comando de "PASO 1" en Cursor y envía.**

Superpowers se activará automáticamente porque:
- ✅ Detectará que tienes especificación completa
- ✅ Saltará brainstorming (Fase 1)
- ✅ Iniciará con Git Worktrees (Fase 2)
- ✅ Generará plan detallado (Fase 3)

**En 5 minutos tendrás el plan completo de implementación.**

**¿Listo para copiar el comando y empezar? 🚀**
