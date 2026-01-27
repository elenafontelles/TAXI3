# 🚕 TAXI API - Sistema de Gestión y Facturación

Sistema centralizado para consolidar la facturación de **3 taxis** desde múltiples plataformas (Uber, FreeNow, Prima) con sincronización diaria automática y dashboard de análisis.

## 📋 Propietarios

- **J. Iván Tintoré** - 2 taxis
- **Elena Fontelles** - 1 taxi

## 🎯 Objetivos

- **Control contable/fiscal**: Datos ordenados para impuestos y gestoría
- **Análisis de rentabilidad**: Identificar qué plataformas y horarios son más rentables
- **Dashboard completo**: Visualización en tiempo real del negocio

## 🛠 Stack Tecnológico

- **Frontend**: React + Recharts
- **Backend**: Python 3.11+ / FastAPI
- **Database**: PostgreSQL 15+
- **Scheduler**: Celery + Redis
- **Deployment**: Docker + Docker Compose

## 📁 Documentación

- [**TAXI_API_SPEC.md**](./TAXI_API_SPEC.md) - Especificación completa del proyecto (1900+ líneas)
  - Arquitectura y modelo de datos
  - Fuentes de datos (Uber, FreeNow, Prima)
  - Seguridad y compliance (GDPR/LOPD)
  - API Contract y endpoints
  - Observability y alerting
  - Testing strategy

- [**PLANTILLA_NUEVO_PROYECTO_v7.md**](./PLANTILLA_NUEVO_PROYECTO_v7.md) - Guía de desarrollo con Claude
  - Basada en proyectos reales (KYC+AML, Intrastat Manager)
  - SOLID principles, Clean Architecture, TDD
  - Mejores prácticas de seguridad y deployment

## 🚀 Estado del Proyecto

**Fase Actual**: Especificación y Diseño ✅

### ✅ Completado

- [x] Especificación técnica completa (aprobada por Gemini 2.5 Pro + GPT-5.1 Codex)
- [x] Arquitectura definida (Clean Architecture)
- [x] Modelo de datos completo (PostgreSQL)
- [x] Plan de seguridad (OAuth, GDPR/LOPD, DSR)
- [x] Observability strategy (Prometheus, Grafana, Alertmanager)

### 🔴 Próximos Pasos (Prioridad ALTA)

| # | Tarea | Responsable | Estado |
|---|-------|-------------|--------|
| 1 | **CRÍTICO:** Verificar automatización real de Prima (exportación programada o API) | Iván | ⬜ Pendiente |
| 2 | **CRÍTICO:** Verificar automatización FreeNow (contactar soporte empresarial) | Iván | ⬜ Pendiente |
| 3 | Acceder a Prima cloud y exportar CSV de prueba manual | Iván | ⬜ Pendiente |
| 4 | Acceder a [portal.free-now.com](https://portal.free-now.com/) y descargar CSV | Iván/Elena | ⬜ Pendiente |
| 5 | Registrar app en [developer.uber.com](https://developer.uber.com) y verificar rate limits/data retention | Iván | ⬜ Pendiente |

## 📊 Fuentes de Datos

| Plataforma | Método | Estado |
|------------|--------|--------|
| **Uber** | API REST OAuth | ⚠️ Verificar rate limits |
| **FreeNow** | CSV Portal | ⚠️ Semi-manual (por confirmar automatización) |
| **Prima** | CSV Cloud | ⚠️ **CRÍTICO** - Verificar si es realmente automático |

## 🔒 Seguridad

- OAuth 2.0 para Uber API
- Tokens encriptados en base de datos
- Política de retención GDPR/LOPD compliant
- Data Subject Requests (DSR) workflow implementado
- Rate limiting y input validation

## 📈 Métricas y Observability

- Prometheus metrics (sync, API, business)
- Grafana dashboards
- Alertmanager (Telegram/Email)
- SLOs: Sync uptime 99.5%, API availability 99.9%

## 🧪 Testing

- Unit tests (pytest) - Objetivo: >80% cobertura
- Integration tests (testcontainers)
- E2E tests (API endpoints)
- Property-based tests (hypothesis - deduplication logic)

## 📝 Versión

**v1.0** - Especificación inicial (27 Enero 2026)

---

> **Documento generado por Claude para Ivan Tintoré**  
> **27 Enero 2026**
