# Integración de Nuevos Casos de Uso con Cassandra

## ✅ Casos de Uso Implementados

### CU 4: Propiedades Disponibles en una Fecha Específica
**Tabla Cassandra**: `propiedades_disponibles_por_fecha`
**Primary Key**: `((fecha), propiedad_id) WITH CLUSTERING ORDER BY (propiedad_id ASC)`

**Funcionalidad**:
- Búsqueda optimizada de propiedades disponibles por fecha
- Incluye datos completos de la propiedad (título, precio, capacidad, tipo)
- Sincronización automática con PostgreSQL

**Comando CLI**:
```bash
python main.py properties buscar-disponibles --fecha 2025-12-25 --ciudad-id 1
```

---

### CU 5: Reservas por (Fecha, Ciudad)
**Tabla Cassandra**: `reservas_por_ciudad_fecha`
**Primary Key**: `((ciudad_id), fecha, reserva_id) WITH CLUSTERING ORDER BY (fecha ASC)`

**Funcionalidad**:
- Consulta rápida de reservas por ciudad y rango de fechas
- Incluye datos completos de la reserva
- Útil para analytics y reporting por ciudad

**Comando CLI**:
```bash
python main.py properties reservas-ciudad --ciudad-id 1 --fecha-inicio 2025-01-01 --fecha-fin 2025-12-31
```

---

### CU 6: Reservas por (Host, Fecha)
**Tabla Cassandra**: `reservas_por_host_fecha`
**Primary Key**: `((host_id), fecha, reserva_id) WITH CLUSTERING ORDER BY (fecha ASC, reserva_id ASC)`

**Funcionalidad**:
- Consulta rápida de reservas por host y rango de fechas
- Incluye datos completos de la reserva
- Útil para panel del host y gestión de propiedades

**Comando CLI**:
```bash
python main.py properties reservas-host --host-id 5 --fecha-inicio 2025-01-01 --fecha-fin 2025-12-31
```

---

## 🔄 Sincronización Automática

### En Disponibilidad
- **Al marcar disponible**: Se agrega a `propiedades_disponibles_por_fecha`
- **Al marcar no disponible**: Se remueve de `propiedades_disponibles_por_fecha`
- **Integración completa** con funciones existentes de disponibilidad

### En Reservas
- **Al crear reserva**: Se agrega a `reservas_por_host_fecha` y `reservas_por_ciudad_fecha`
- **Al cancelar reserva**: Se remueve de ambas tablas
- **Sincronización automática** en `ReservationService.create_reservation()`

---

## 📋 Estructura de Datos

### Propiedades Disponibles
```json
{
  "fecha": "2025-12-25",
  "propiedad_id": 29,
  "ciudad_id": 1,
  "titulo": "Casa en el centro",
  "precio_noche": 150.0,
  "capacidad": 4,
  "tipo_propiedad": "Casa completa",
  "disponible": true
}
```

### Reservas por Host/Ciudad
```json
{
  "host_id": 5,  // o ciudad_id para la otra tabla
  "fecha": "2025-12-25",
  "reserva_id": 123,
  "propiedad_id": 29,
  "huesped_id": 10,
  "fecha_inicio": "2025-12-25",
  "fecha_fin": "2025-12-28",
  "estado": "confirmada",
  "precio_total": 450.0,
  "created_at": "2025-11-17T01:41:00Z"
}
```

---

## 🚀 Funciones Principales

### En `db/cassandra.py`
- `get_propiedades_disponibles_por_fecha(fecha, ciudad_id, limit)`
- `get_reservas_por_host_fecha(host_id, fecha_inicio, fecha_fin, limit)`
- `get_reservas_por_ciudad_fecha(ciudad_id, fecha_inicio, fecha_fin, limit)`
- `cassandra_add_reserva(reserva_data)`
- `cassandra_remove_reserva(reserva_data)`

### En `services/reservations.py`
- `get_propiedades_disponibles_fecha(fecha, ciudad_id)`
- `get_reservas_host(host_id, fecha_inicio, fecha_fin)`
- `get_reservas_ciudad(ciudad_id, fecha_inicio, fecha_fin)`

### Comandos CLI
- `python main.py properties buscar-disponibles`
- `python main.py properties reservas-host`
- `python main.py properties reservas-ciudad`

---

## 📊 Ventajas del Diseño

1. **Performance**: Las claves primarias están optimizadas para los patrones de consulta
2. **Escalabilidad**: Distribución eficiente de datos por fecha y entidad
3. **Consistencia**: Sincronización automática con PostgreSQL
4. **Flexibilidad**: Soporte para rangos de fechas y filtros opcionales
5. **Analytics**: Datos listos para reporting y análisis

---

## ✅ Estado de Integración

- [x] Tablas de Cassandra diseñadas con claves primarias optimizadas
- [x] Funciones de sincronización automática implementadas
- [x] Integración con servicios existentes completada
- [x] Comandos CLI disponibles y funcionales
- [x] Gestión completa del ciclo de vida de datos
- [x] Error handling y logging implementado
- [x] Compatibilidad con arquitectura multi-base de datos existente

**Total**: 3 nuevos casos de uso completamente integrados con Cassandra 🎉