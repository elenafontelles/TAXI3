# TAXI2 - Descripcion Funcional del Producto

**Version**: 1.0
**Fecha**: Febrero 2026
**Autor**: Producto

---

## 1. Vision General

TAXI2 es una plataforma de gestion integral para flotas de taxi que resuelve un problema critico del sector: **el calculo diario de la liquidacion entre propietario y conductor**.

Un propietario de licencias de taxi trabaja con varios conductores que operan en multiples plataformas simultaneamente (taximetro propio, FreeNow, Uber). Cada dia, el conductor recauda dinero en efectivo, por tarjeta y a traves de apps. Al final de cada periodo, propietario y conductor deben ajustar cuentas: cuanto ha recaudado el conductor, cuanto le corresponde segun su porcentaje, cuanto ha adelantado ya, y cuanto queda pendiente.

**Antes de TAXI2**, este proceso se hacia manualmente con hojas de calculo, cruzando datos de 6 fuentes distintas. Era lento, propenso a errores y generaba conflictos.

**Con TAXI2**, todo el proceso esta automatizado: los datos se importan, se cruzan y se calcula la liquidacion al instante.

---

## 2. Usuarios del Sistema

### Propietario / Administrador

El propietario de las licencias de taxi es el usuario principal. Gestiona toda la operativa:

- Sube los archivos de datos de cada plataforma
- Lanza la descarga automatica de datos desde FreeNow y Prima
- Calcula las liquidaciones de cada conductor
- Exporta los informes para entregarlos a los conductores
- Consulta el dashboard de rendimiento mensual
- Valida las incidencias detectadas automaticamente
- Gestiona los datos de conductores y vehiculos

### Conductor

Los conductores tienen acceso limitado al sistema para consultar su propia informacion:

- Ven el dashboard con sus KPIs del mes en curso
- Consultan su historial de viajes

---

## 3. Modulos Funcionales

### 3.1 Dashboard - Panel de Control Mensual

**Que es**: La pantalla principal del sistema. Muestra una comparativa mensual del rendimiento de todos los conductores.

**Para que sirve**: Permite al propietario ver de un vistazo como va el mes, comparar conductores entre si y detectar tendencias.

**Que informacion muestra**:

- **Ingresos por plataforma**: Cuanto ha recaudado cada conductor en Prima (taximetro), FreeNow y Uber, con el total neto
- **Dias trabajados y viajes realizados**: Actividad de cada conductor
- **Kilometros recorridos**: Km ocupados (con pasajero) y km en vacio, con la tasa de ocupacion
- **Eficiencia**: Euros por kilometro, euros por viaje y promedio diario
- **Mix de plataformas**: Que porcentaje del ingreso viene de cada plataforma (grafico de barras)
- **Combustible**: Gasto total, litros consumidos, precio por litro, porcentaje del combustible sobre la recaudacion y coste por km

**Periodo**: Siempre muestra el mes en curso (del dia 1 hasta hoy).

---

### 3.2 Subir Archivos - Importacion de Datos

**Que es**: La pantalla donde el administrador sube los archivos de datos de cada plataforma.

**Para que sirve**: Alimentar al sistema con los datos necesarios para calcular las liquidaciones.

**Archivos que se pueden subir**:

| Archivo | Plataforma | Que contiene |
|---------|-----------|-------------|
| CSV de FreeNow | FreeNow | Todos los viajes realizados a traves de la app FreeNow |
| CSV de Prima | Prima (Taxitronic) | Todos los viajes registrados en el taximetro |
| CSV de Uber | Uber | Resumen diario de pagos de Uber |
| Extracto La Caixa | Banco (XLSX) | Movimientos bancarios con los cobros de tarjeta VISA del TPV del taxi |
| CSV Petroprix | Gasolinera | Repostajes de combustible en Petroprix |
| XLSX Repsol/Solred | Gasolinera | Repostajes de combustible en Repsol |

**Como funciona**:

1. Seleccionar la plataforma en el desplegable
2. Opcionalmente, seleccionar conductor y vehiculo (si no, el sistema los detecta automaticamente)
3. Arrastrar el archivo o seleccionarlo manualmente
4. Pulsar "Subir y Procesar"

**Comportamiento de reemplazo**: Si se sube un archivo que cubre un rango de fechas que ya tiene datos, los datos anteriores se reemplazan por los nuevos. Esto permite corregir errores simplemente volviendo a subir el archivo correcto.

**Deteccion automatica**: El sistema identifica automaticamente a que conductor y vehiculo pertenece cada registro del archivo, cruzando nombres, matriculas y numeros de licencia.

#### Entrada manual: Otros Gastos

Debajo del formulario de subida hay un apartado para registrar gastos extraordinarios de un conductor (ej: pinchazo, lavado, peaje). Se introduce:
- Conductor
- Fecha
- Importe
- Concepto

Estos gastos se descuentan del anticipado en la liquidacion.

#### Entrada manual: Otros / Incentivos FreeNow

Apartado para registrar importes adicionales de FreeNow que no aparecen en el CSV de viajes:
- **Otros**: Cargos o descuentos adicionales de FreeNow
- **Incentivos**: Bonificaciones o promociones de FreeNow

Cada valor se introduce con su fecha e importe. Si se introduce un nuevo valor para un dia que ya tiene datos, el nuevo **sustituye** al anterior (no se acumulan). Se puede poner 0 para eliminar un importe previo.

Estos importes se suman tanto al campo "FreenowT3" como al campo "AppFN" en la liquidacion.

---

### 3.3 Sincronizacion - Descarga Automatica de Datos

**Que es**: Pantalla para lanzar la descarga automatica de datos desde los portales web de FreeNow y Prima.

**Para que sirve**: Evitar tener que descargar manualmente los archivos CSV desde cada portal. El sistema entra automaticamente en los portales, descarga los datos y los importa.

**Plataformas con descarga automatica**:

| Boton | Que hace |
|-------|---------|
| **Sincronizar FreeNow 092/1061** | Descarga los viajes de la cuenta FreeNow que gestiona las licencias 092 y 1061 |
| **Sincronizar FreeNow 361** | Descarga los viajes de la segunda cuenta FreeNow (licencia 361) |
| **Sincronizar Prima** | Descarga los viajes del taximetro desde el portal Prima/Taxitronic |

**Como funciona**:

1. Seleccionar el rango de fechas (por defecto, la ultima semana)
2. Pulsar el boton de la plataforma deseada
3. El sistema lanza un proceso en segundo plano que:
   - Abre un navegador automatizado
   - Inicia sesion en el portal
   - Navega hasta la seccion de descarga
   - Configura las fechas
   - Descarga el archivo
   - Lo importa automaticamente
4. El estado aparece en el historial de sincronizaciones

**Informacion mostrada**:
- Estado de la ultima sincronizacion de cada plataforma
- Archivos descargados (con opcion de ver su contenido)
- Historial de sincronizaciones con resultado (exito/error, registros creados/omitidos)

---

### 3.4 Liquidacion - Calculo de Liquidacion Conductor-Propietario

**Que es**: El modulo central del sistema. Calcula cuanto debe cobrar o pagar cada conductor al propietario por un periodo determinado.

**Para que sirve**: Automatizar el ajuste de cuentas diario entre propietario y conductor.

#### Como se usa

1. Seleccionar el conductor
2. Seleccionar el rango de fechas
3. Opcionalmente, ajustar la hora de inicio del primer dia (por defecto 00:00)
4. El sistema muestra una tabla con el desglose dia a dia

#### Que muestra la tabla de liquidacion

Para cada dia se calculan y muestran los siguientes campos:

| Campo | Que significa |
|-------|--------------|
| **Prima** | Lo recaudado en el taximetro (viajes de calle y de app que pasan por taximetro) |
| **Inc** (Incidencias) | Importe de viajes detectados como posibles tiquets nulos, que se restan de la recaudacion |
| **FreenowT3** | Lo recaudado a traves de FreeNow (viajes con tarifa fija + ajustes manuales). Si el conductor asume la comision de FreeNow, ya esta descontada |
| **Uber T3** | Lo recaudado a traves de Uber |
| **Rec. Neta** | Recaudacion neta del dia: Prima + FreenowT3 + Uber T3 - Incidencias |
| **%** | Porcentaje que le corresponde al conductor (40% o 45% segun el umbral) |
| **TPV** | Total cobrado por tarjeta/VISA en el taxi (dato del extracto bancario La Caixa) |
| **App FN** | Lo que FreeNow ha pagado por transferencia (viajes pagados por app + ajustes manuales) |
| **App Uber** | Lo que Uber ha pagado por transferencia |
| **Cash** | Efectivo que tiene el conductor en mano al final del dia |
| **IVA** | IVA (10%) incluido en la recaudacion neta |
| **Parte Prop.** | La parte proporcional que le corresponde al conductor: base imponible x su porcentaje |
| **Gasolina** | Gasto en combustible del dia |
| **Otros** | Otros gastos registrados manualmente |
| **Anticipado** | Lo que el conductor ya ha adelantado al propietario (recaudacion neta menos lo cobrado por app, tarjeta y gastos) |
| **Liquidacion** | **Resultado final**: Parte proporcional - Anticipado |

#### Interpretacion del resultado

- **Liquidacion positiva**: El conductor ha adelantado mas de lo que le corresponde. **El propietario le debe dinero.**
- **Liquidacion negativa**: El conductor ha recaudado mas de lo que le corresponde (normalmente en efectivo). **El conductor debe dinero al propietario.**

Al final de la tabla se muestra una **fila de totales** con la suma de todo el periodo.

#### Configuracion por conductor

Cada conductor tiene su propia configuracion de comisiones, que se establece en la pantalla de Administracion:

| Parametro | Descripcion | Ejemplo |
|-----------|-------------|---------|
| **Porcentaje base** | Porcentaje del conductor cuando no alcanza el umbral | 40% |
| **Porcentaje bonus** | Porcentaje del conductor cuando supera el umbral | 45% |
| **Umbral** | Recaudacion neta diaria a partir de la cual se aplica el bonus | 300 EUR |
| **Comision FreeNow** | Quien asume la comision de FreeNow (0% = propietario, 100% = conductor) | 0% o 100% |
| **Gasolina descontada** | Si la gasolina se descuenta del anticipado del conductor | Si / No |

#### Exportacion

Desde la pantalla de liquidacion se puede exportar el informe en dos formatos:

- **Excel (.xlsx)**: Archivo con las mismas 17 columnas, formateado con cabeceras en azul y fila de totales
- **PDF**: Documento en formato apaisado A4, listo para imprimir y entregar al conductor

---

### 3.5 Viajes - Consulta de Viajes

**Que es**: Listado paginado de todos los viajes registrados en el sistema.

**Para que sirve**: Consultar el detalle de viajes individuales, buscar viajes concretos y verificar que los datos importados son correctos.

**Filtros disponibles**:
- Rango de fechas
- Plataforma (Prima, FreeNow, Uber)
- Conductor (solo para administradores; los conductores solo ven los suyos)

**Informacion por viaje**: Fecha/hora, plataforma (con etiqueta de color), conductor, importe bruto e importe neto.

**Ordenacion**: Se puede ordenar por cualquier columna haciendo clic en la cabecera.

---

### 3.6 Validacion de Incidencias

**Que es**: Cola de revision de viajes sospechosos detectados automaticamente.

**Para que sirve**: Revisar los viajes que el sistema ha identificado como posibles tiquets nulos (el taximetro se abrio y cerro sin realizar un viaje real).

**Criterio de deteccion**: Un viaje se marca como sospechoso si tiene 0 km recorridos y duro menos de 30 segundos.

**Como funciona**:

1. Al importar datos de Prima, el sistema detecta automaticamente estos viajes
2. Aparecen en la pantalla de Validacion como "pendientes"
3. El administrador revisa cada uno y decide:
   - **Valido**: Es una incidencia real (tiquet nulo). Su importe se restara de la recaudacion en la liquidacion.
   - **Invalido**: No es una incidencia (fue un viaje legitimo). Se ignora en la liquidacion.

---

### 3.7 Administracion - Gestion de Conductores y Vehiculos

**Que es**: Pantalla de gestion de los datos maestros del sistema.

**Conductores - datos editables**:
- Nombre, email, telefono
- Numero de licencia (formato: "361 - 0397MSS")
- Porcentaje base y bonus
- Umbral de comision
- Porcentaje de comision FreeNow que asume el conductor
- Si la gasolina se descuenta del conductor

**Vehiculos - datos editables**:
- Matricula
- Numero de licencia
- Marca, modelo y año

---

### 3.8 Exportacion de Datos

**Que es**: Pantalla para descargar datos en formato CSV.

**Opciones de exportacion**:
- **Viajes**: Exporta el listado de viajes filtrado por fecha y conductor
- **Resumen diario**: Exporta un resumen agregado por dia con totales de viajes, km, bruto, comision y neto

---

### 3.9 Resumen - Vista Resumida

**Que es**: Vista de resumen diario con KPIs agregados.

**Que muestra**:
- Tarjetas resumen: total de viajes, recaudacion bruta, comision total, km totales
- Tabla con desglose diario por conductor y vehiculo

---

## 4. Conceptos Clave del Negocio

### 4.1 Plataformas y sus roles

```
TAXIMETRO (Prima)
  El taximetro registra TODOS los viajes: los de calle, los de FreeNow
  y los de Uber. Es la fuente principal de datos de actividad.

FREENOW
  App de movilidad. El pasajero pide un taxi por la app.
  Dos modalidades:
  - FIXED: FreeNow cobra una tarifa fija al pasajero. El taximetro
    no se usa para el cobro (aunque puede registrar el viaje).
    Este importe se suma a la recaudacion.
  - METERED: FreeNow conecta al pasajero pero el cobro va por
    taximetro. El importe ya esta en Prima, NO se suma otra vez.

  Comision FreeNow: 12,5% del importe bruto + 21% IVA sobre la comision.
  Segun la configuracion, la asume el propietario o el conductor.

UBER
  Similar a FreeNow. Los datos se importan como resumen diario
  (no viaje a viaje). Se usa el campo "T3 fijo" como importe
  que suma a la recaudacion.

LA CAIXA (TPV/VISA)
  El extracto bancario muestra los cobros diarios por tarjeta
  en el taxi. Este dato es necesario para calcular el efectivo
  que tiene el conductor.

COMBUSTIBLE (Petroprix / Repsol)
  Los repostajes se importan para controlar el gasto en gasolina
  y, si esta configurado, descontarlo del anticipado del conductor.
```

### 4.2 El ciclo de la liquidacion

```
    CONDUCTOR TRABAJA UN DIA
            |
            v
    Recauda dinero de 3 fuentes:
    - Efectivo de pasajeros de calle
    - Pagos por tarjeta (TPV)
    - Viajes de FreeNow y Uber (pagados por app)
            |
            v
    Al final del dia:
    - Parte del dinero ya esta "adelantado":
      * Lo cobrado por tarjeta (TPV) va al banco del propietario
      * Lo cobrado por FreeNow app va por transferencia
      * Lo cobrado por Uber va por transferencia
    - El conductor tiene en mano el EFECTIVO
            |
            v
    LIQUIDACION:
    1. Se suma todo lo recaudado (recaudacion neta)
    2. Se calcula la parte que le corresponde al conductor
       (su porcentaje sobre la base imponible)
    3. Se resta lo que ya ha "adelantado" (TPV + apps + gastos)
    4. La diferencia es la LIQUIDACION:
       - Si es positiva: el propietario le paga al conductor
       - Si es negativa: el conductor paga al propietario
         (normalmente entregando parte del efectivo)
```

### 4.3 Cuentas FreeNow

El sistema gestiona dos cuentas de FreeNow porque las licencias de taxi estan repartidas:

| Cuenta | Licencias | Conductores |
|--------|-----------|-------------|
| Cuenta 1 | 092, 1061 | Los asignados a estas licencias |
| Cuenta 2 | 361 | Los asignados a esta licencia |

Los CSV de cada cuenta se suben por separado, y la sincronizacion automatica tiene botones independientes para cada una.

### 4.4 Deteccion de incidencias

El sistema detecta automaticamente viajes que podrian ser "tiquets nulos": el taximetro se inicio y se cerro inmediatamente sin recorrer distancia. Estos viajes generan un importe en el taximetro que no corresponde a un servicio real.

Criterio: **0 km recorridos** y **duracion menor a 30 segundos**.

Estos viajes quedan pendientes de revision. Si el administrador los confirma como incidencia, su importe se resta de la recaudacion del conductor ese dia.

---

## 5. Flujo de Trabajo Tipico

### Flujo mensual del administrador

```
INICIO DE MES
     |
     v
Cada dia o cada pocos dias:
  1. Sincronizar FreeNow (automatico) --> boton en Sincronizacion
  2. Sincronizar Prima (automatico) --> boton en Sincronizacion
  3. Revisar incidencias detectadas --> pantalla Validacion
     |
     v
Cuando se recibe el archivo de Uber:
  4. Subir CSV de Uber --> pantalla Subir Archivos
     |
     v
A final de mes (o del periodo de liquidacion):
  5. Subir extracto La Caixa (XLSX) --> pantalla Subir Archivos
  6. Subir datos de combustible --> pantalla Subir Archivos
  7. Registrar ajustes FreeNow (otros/incentivos) si los hay
  8. Registrar otros gastos si los hay
     |
     v
  9. Ir a Liquidacion
  10. Seleccionar conductor y rango de fechas
  11. Revisar la tabla de liquidacion
  12. Exportar a Excel o PDF
  13. Entregar informe al conductor
     |
     v
  14. Consultar el Dashboard para ver el rendimiento comparativo
```

### Flujo diario del conductor

```
  1. Acceder al sistema con su email y contraseña
  2. Ver el Dashboard con sus KPIs del mes
  3. Opcionalmente, consultar sus viajes en la pantalla Viajes
```

---

## 6. Glosario

| Termino | Definicion |
|---------|-----------|
| **Prima** | Marca del taximetro (Taxitronic). Se usa como sinonimo de "datos del taximetro" |
| **FreeNow** | App de movilidad (antes MyTaxi). Los pasajeros piden taxi por la app |
| **FIXED** | Modalidad de FreeNow donde la tarifa es fija (no usa taximetro para el cobro) |
| **METERED** | Modalidad de FreeNow donde se usa el taximetro para determinar el precio |
| **TPV** | Terminal Punto de Venta. El datafono del taxi donde se cobra con tarjeta |
| **T3** | Tarifa 3. En el contexto de Uber y FreeNow, es el importe que efectivamente se suma a la recaudacion |
| **Recaudacion** | Total de ingresos del dia por todos los conceptos |
| **Recaudacion neta** | Recaudacion menos incidencias |
| **Base imponible** | Recaudacion neta sin IVA |
| **Parte proporcional** | Lo que le corresponde al conductor: base imponible x su porcentaje |
| **Anticipado** | Dinero que el conductor ya ha "adelantado" al propietario (cobros que van directamente al propietario: tarjeta, apps, gastos) |
| **Liquidacion** | Resultado final: parte proporcional - anticipado. Si es positivo, el propietario debe al conductor; si es negativo, el conductor debe al propietario |
| **Incidencia** | Viaje sospechoso de ser un tiquet nulo (0 km, menos de 30 segundos) |
| **Comision FreeNow** | 12,5% del importe bruto + 21% IVA. La puede asumir el propietario o el conductor segun configuracion |
| **Umbral de bonus** | Recaudacion neta diaria a partir de la cual el conductor cobra un porcentaje mayor |
| **Licencia** | Numero de la licencia del taxi (ej: 092, 361, 1061) |
