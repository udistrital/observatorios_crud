# PROY-ASIS-001 — Enrutamiento API y segmentación por apps

## Historia de Usuario (AS-IS)
**Como** consumidor institucional de la API de observatorios
**Quiero** contar con rutas versionadas y organizadas por dominio
**Para** integrar cliente y servicios MID sin ambigüedad en contratos.

## Criterios de aceptación funcionales
1. Dado un consumidor API, cuando consulta recursos, entonces encuentra rutas bajo `api/<str:version>/...`.
2. Dado el backend CRUD, cuando expone módulos de dominio, entonces mantiene segmentación por app (`apps/*/urls.py`).
3. Dada la necesidad de exploración técnica, cuando se requiere documentación, entonces existen rutas Swagger y ReDoc.

---

## Problema funcional
Sin una referencia AS-IS compacta del enrutamiento global, el análisis de impacto en cambios de endpoint se vuelve costoso y propenso a errores entre repositorios consumidores.

## Objetivo del usuario
Disponer de una especificación verificable del enrutamiento actual para soportar mantenimiento y evolución controlada.

## Impacto institucional
- Reduce regresiones en integraciones con `observatorios_cliente` y `observatorios_mid`.
- Mejora trazabilidad de cambios en contratos API.

---

## Soporte técnico
### Contratos y endpoints observados
- Prefijo global: `api/<str:version>/...`
- Documentación: `/documentacion/swagger/` y `/documentacion/redoc/`

### Evidencia verificable
- `osiris/osiris/urls.py`
- `osiris/apps/*/urls.py`
- `README.md` (Endpoints útiles)

### Dependencias
- Django URL dispatcher
- DRF y `drf_yasg`

### Riesgos
- **INFERENCIA:** no se evidencia enrutador global con validación estricta de valores permitidos para `version`; el control puede recaer en cada app/consumidor.

## Relación con documentación histórica
- Esta spec consolida la convención vigente `PROY-ASIS-*`.
- El detalle ampliado histórico permanece en `docs/specs/CRUD-ASIS-001_enrutamiento_api_v1.md`.
