# CRUD-ASIS-001 — Enrutamiento API y segmentación por apps

## Historia de Usuario (AS-IS)
**Como** consumidor institucional de la API
**Quiero** contar con rutas estables y segmentadas por dominio
**Para** integrar funcionalidades sin ambigüedad de endpoints.

## Criterios de aceptación funcionales
- Dado un consumidor autorizado, cuando consulta recursos, entonces encuentra rutas bajo versión API consistente.
- Dado un módulo de dominio, cuando se expone, entonces conserva segmentación clara por app.

## 1. Contexto
El backend CRUD publica endpoints por app de dominio bajo prefijos versionados `api/<version>/`.

## 2. Problema
No existe especificación única del enrutamiento central, lo que dificulta análisis de impacto.

## 3. Objetivo
Documentar la organización AS-IS de rutas y módulos expuestos.

## 4. Alcance
### Incluye
- Rutas de documentación Swagger/ReDoc.
- Inclusión de rutas para datos, observatorios, factores, características, aspectos, estructuras, campos, dashboards y gráficos.
### Excluye (Fuera de alcance)
- Lógica interna de cada ViewSet.

## 5. Actores
- Consumidores API (cliente y MID).
- Router Django.

## 6. Flujo principal
1. Solicitud ingresa por URL global.
2. `urls.py` despacha a app por prefijo.
3. App resuelve recurso y método.

## 7. Flujos alternos / excepciones
- A1: Version inválida puede enrutar a app sin validación semántica explícita.
- **INFERENCIA**: no se observa restricción estricta de valores de versión en enrutador global.

## 8. Reglas de negocio
- RN-01: Todo recurso de dominio usa patrón `api/<str:version>/...`.
- RN-02: Exposición de documentación técnica está habilitada públicamente.

## 9. Contratos técnicos
- Archivo de enrutamiento central Django.
- Integración con `drf_yasg` para documentación.

## 10. Criterios de aceptación verificables
- [ ] Existe registro explícito de apps de dominio en `urlpatterns`.
- [ ] Documentación Swagger/ReDoc responde en rutas configuradas.

## 11. Dependencias
- `apps/*/urls.py`
- `drf_yasg`

## 12. Riesgos
- Superficie de cambio alta en `urls.py` por acoplamiento transversal.

## 13. Pendientes
- Definir política de versionado semántico y deprecación de endpoints.

## 14. Evidencia
- `observatorios_crud/osiris/osiris/urls.py`

## 15. Clasificación SDD
- Tipo: AS-IS
- Tamaño relativo: S
- Prioridad: Alta
