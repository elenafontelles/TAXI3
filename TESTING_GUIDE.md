# TAXI API - Guia de Validacion

**Fecha:** 2026-02-08
**Validadora:** Elena Fontelles
**URL:** https://keonycs.com/tools3/taxi/

---

## Acceso

1. Ir a https://keonycs.com/tools3/taxi/
2. Login con `elenafontelles@gmail.com` / `DrkRqaoxUjVk`
3. Deberia redirigir al Dashboard

---

## 1. Dashboard (/)

- [ ] Se ve el resumen de earnings (hoy, semana, mes)
- [ ] Se ve el grafico de barras con ingresos diarios
- [ ] Se ven los viajes recientes
- [ ] Se ve la seccion de analytics avanzado (EUR/km, EUR/hora)

---

## 2. Viajes (/trips)

- [ ] Se ve la lista de viajes con paginacion
- [ ] Los filtros funcionan (fecha, conductor, plataforma, metodo de pago)
- [ ] Boton "Nuevo viaje Uber" (entrada manual) funciona (solo admin)

---

## 3. Sync (/sync)

- [ ] Se ve el estado del ultimo sync de FreeNow y Prima
- [ ] Boton "Sync FreeNow" encola el job (no hace falta esperar a que termine)
- [ ] Boton "Sync Prima" encola el job
- [ ] Boton "Cross-match" ejecuta el vinculado Prima <-> App
- [ ] Se ven los logs de sync anteriores
- [ ] El file browser muestra los CSVs importados

---

## 4. Upload (/upload)

### 4a. Viajes
- [ ] Subir un CSV de **Uber** → se importan los viajes
- [ ] Subir un CSV de **FreeNow** → se importan con auto-match conductor/vehiculo
- [ ] Subir un CSV de **Prima** → se importan con match por licencia
- [ ] Si se sube un CSV con columnas incorrectas → muestra error de validacion

### 4b. Pagos VISA
- [ ] Subir un XLSX de **La Caixa** → se importan los pagos VISA
- [ ] Los pagos se emparejan automaticamente con viajes (±10 min)

### 4c. Combustible
- [ ] Subir un CSV de **Petroprix** → se importan gastos con auto-match matricula
- [ ] Subir un PDF de **Repsol/Solred** → se importan gastos con auto-match matricula

---

## 5. Admin (/admin)

- [ ] Se ven las listas de conductores, vehiculos y propietarios
- [ ] Se puede editar un conductor (nombre, email, comisiones)
- [ ] Se puede editar un vehiculo (matricula, modelo, marca)
- [ ] Los campos de comision aparecen: base %, bonus %, threshold

---

## 6. Validacion (/validacion)

Tiene 3 pestanas:

- [ ] **Incidencias:** viajes con 0 km y <30 segundos (tickets nulos)
- [ ] **VISA sin match:** pagos VISA que no se emparejaron con ningun viaje
- [ ] **Combustible sin match:** gastos que no se asignaron a vehiculo
- [ ] Se puede marcar cada item como "Valido" o "Invalido"

---

## 7. Liquidacion (/liquidacion)

- [ ] Seleccionar conductor y rango de fechas
- [ ] Se muestra la tabla de liquidacion diaria
- [ ] Los calculos incluyen: bruto, comision plataforma, neto, IVA, comision conductor
- [ ] Boton **"Exportar Excel"** descarga un .xlsx
- [ ] Boton **"Exportar PDF"** descarga un .pdf

---

## 8. Summary (/summary)

- [ ] Se ven las agregaciones diarias (viajes, km, ingresos por conductor)
- [ ] Los filtros de fecha funcionan
- [ ] Los filtros de conductor y vehiculo funcionan
- [ ] Se ven los totales al final

---

## 9. Export (/export)

- [ ] Exportar **viajes detallados** en CSV
- [ ] Exportar **viajes detallados** en Excel
- [ ] Exportar **resumen diario** en CSV
- [ ] Exportar **resumen diario** en Excel

---

## 10. API REST (/api/v1/)

Para probar con curl o Postman:

```bash
# Login (obtener token)
curl -X POST https://keonycs.com/tools3/taxi/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"elenafontelles@gmail.com","password":"DrkRqaoxUjVk"}'

# Listar viajes (usar el token devuelto)
curl https://keonycs.com/tools3/taxi/api/v1/trips \
  -H "Authorization: Bearer <token>"

# Resumen diario
curl https://keonycs.com/tools3/taxi/api/v1/summary/daily \
  -H "Authorization: Bearer <token>"
```

- [ ] Login devuelve un token JWT
- [ ] GET /trips devuelve viajes en JSON
- [ ] GET /summary/daily devuelve agregaciones
- [ ] GET /drivers devuelve lista de conductores (solo admin)

---

## 11. Automatizaciones (no requieren accion manual)

Estas tareas se ejecutan solas. Verificar que no dan error en los logs:

| Job | Horario (UTC) | Que hace |
|-----|---------------|----------|
| Sync FreeNow | 02:00 | Descarga viajes del dia anterior |
| Sync Prima | 02:05 | Descarga viajes del dia anterior |
| GDPR cleanup | 03:00 | Anonimiza GPS de viajes >90 dias |
| Gap check | 08:00 | Alerta si >3 dias sin sync |

Para ver los logs:
```bash
ssh ubuntu@51.77.144.212 "sudo docker logs taxi-worker --tail 50"
```

---

## Notas

- La app tiene rate limiting: 60 peticiones/minuto general, 5/min en login, 2/min en sync
- Si algo falla, los logs del servidor estan en:
  ```bash
  sudo docker logs taxi-api --tail 100
  sudo docker logs taxi-worker --tail 100
  ```
- El deploy es automatico al hacer push a main (GitHub Actions)

---

## Bugs conocidos

| Bug | Impacto | Workaround |
|-----|---------|------------|
| Prima conductor codes hardcodeados | Si cambian conductores hay que actualizar el parser | Editar `scripts/parsers/prima_parser.py` |
| Uber no tiene scraper | Los viajes de Uber se suben manualmente | Usar /upload o /trips (entrada manual) |

---

## Mejoras pendientes (ideas)

- [ ] Scraper automatico de Uber
- [ ] Dashboard responsive para movil
- [ ] Alertas por Telegram/WhatsApp
- [ ] Backup automatico de PostgreSQL
- [ ] Facturacion electronica
