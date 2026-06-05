# 🏨 Hotel System — Sistema de Gestión Hotelera
**USS · Taller de Lenguaje de Programación · Proyecto 7**

## Stack
- Python 3.11 + Django 4.2
- PostgreSQL 15 (Docker)
- **Django Templates + Bootstrap 5** (100% server-side)
- Docker + Docker Compose

## Equipo
| Nombre | Módulo |
|---|---|
| Fustamante Sosa Lennart Samuel
## Levantar el proyecto

```bash
# 1. Clonar el repositorio
git clone <repo-url>
cd hotel_system

# 2. Levantar Docker
docker-compose up --build

# 3. Primera vez: crear superusuario
docker-compose exec web python manage.py createsuperuser

# 4. (Opcional) Cargar datos de prueba
docker-compose exec web python manage.py loaddata fixtures/inicial.json
```

## Accesos
| URL | Descripción |
|---|---|
| http://localhost:8000/ | Dashboard recepción |
| http://localhost:8000/admin/ | Panel admin Django |
| http://localhost:8000/reservas/ | Lista de reservas |
| http://localhost:8000/housekeeping/ | Panel limpieza |
| http://localhost:8000/gerencia/ | Reportes y KPIs |

## Estructura
```
hotel_system/
├── apps/
│   ├── usuarios/      → Usuario con roles (admin, recepcionista, housekeeping)
│   ├── recepcion/     → Hotel, TipoHabitacion, Habitacion + mapa visual
│   ├── reservas/      → Huesped, Tarifa, Reserva, Estancia, CargoEstancia, Folio
│   ├── housekeeping/  → TareaLimpieza, IncidenteHabitacion
│   └── gerencia/      → Vistas de reportes y KPIs
├── templates/         → Django Templates por app + base.html
├── static/css/        → hotel.css con estilos del mapa
├── hotel_system/      → settings.py, urls.py
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

## Reglas de negocio implementadas
1. ❌ No check-in en habitación MANTENIMIENTO o LIMPIEZA
2. 💰 Precio calculado con tarifa vigente por temporada (`Tarifa.get_precio_vigente`)
3. 🔒 No checkout con folio PENDIENTE de pago (`estancia.tiene_deuda`)
4. 📅 No solapamiento de reservas activas en la misma habitación (constraint con `Q()`)
5. 🧹 Checkout → habitación pasa automáticamente a LIMPIEZA

## Pantallas implementadas
- Mapa de habitaciones (grid con colores por estado)
- Panel de reservas del día (llegadas / en casa / salidas)
- Nueva reserva con cálculo de tarifa automático
- Check-in con asignación de habitación
- Folio del huésped con cargos y checkout
- Panel housekeeping con botón "Marcar como Lista"
- Reportes de ocupación y revenue (gerencia)
