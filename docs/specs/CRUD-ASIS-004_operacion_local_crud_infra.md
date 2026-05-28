# CRUD-ASIS-004 — Operación local desacoplada (solo CRUD y stack de infraestructura)

## Historia de Usuario (AS-IS)
**Como** desarrollador técnico del ecosistema Observatorios  
**Quiero** levantar de forma independiente la API CRUD y, cuando aplique, la infraestructura local  
**Para** validar cambios funcionales sin bloquearme por dependencias de entorno completas.

## Criterios de aceptación funcionales
- Dado un entorno local con Docker, cuando ejecuto `./run_crud.sh`, entonces se levanta únicamente la API CRUD en `localhost:8000`.
- Dado un entorno local con Docker, cuando ejecuto `./infraestructura/run_infra.sh`, entonces se levanta la infraestructura local (Elasticsearch, Kibana, Nginx).
- Dado un único archivo `osiris/.env`, cuando ajusto `PARAMETER_STORE` (vacío vs definido), entonces la API toma la estrategia de credenciales: local si `PARAMETER_STORE` está vacío, o SSM si está definido.
- Dado que no necesito stack local, cuando apunto a Elasticsearch remoto (p. ej. túnel), entonces puedo ejecutar CRUD sin iniciar `infraestructura/run_infra.sh`.

## 1. Problema funcional
Sin una guía operativa explícita, los equipos asumen que siempre deben levantar todo el stack local, lo que incrementa tiempos de arranque y fricción en validaciones rápidas.

## 2. Objetivo del usuario
Permitir ejecución local por escenarios: (a) solo API CRUD, (b) API + infraestructura local, o (c) API con Elasticsearch remoto.

## 3. Impacto institucional
Reduce tiempos de soporte técnico y habilita ciclos de prueba más cortos para equipos que mantienen integración con `observatorios_cliente` y sincronización con `observatorios_mid`.

## 4. Alcance
### Incluye
- Script operativo de API (`run_crud.sh`).
- Script operativo de infraestructura (`infraestructura/run_infra.sh`).
	- Política de único `.env` en `osiris/.env` y uso de `PARAMETER_STORE` para distinguir local vs entornos con secretos en SSM.

### Excluye (fuera de alcance)
- Ajustes de negocio de endpoints.
- Hardening de seguridad para ambientes productivos.

## 5. Actores
- Desarrollador backend.
- Equipo de soporte/devops local.

## 6. Flujo principal
1. El usuario configura `osiris/.env` desde `osiris/.env.template`.
2. Ejecuta `./run_crud.sh`.
3. El script valida existencia de `.env`, construye imagen y levanta `osiris_back` con `osiris/docker-compose.yml`.

## 7. Flujos alternos / excepciones
- A1: Si no existe `osiris/.env`, el script lo crea desde plantilla y termina para ajuste manual.
- A2: Si falta la red `elastic_net`, `run_crud.sh` puede fallar por red externa no creada.
- A3: Para pruebas con Elastic remoto, se omite `infraestructura/run_infra.sh` y se usa túnel/configuración de host.
- **INFERENCIA**: El consumo sin infraestructura local depende de disponibilidad y latencia del Elasticsearch remoto.

## 8. Reglas de negocio operativas
- RN-01: Si `PARAMETER_STORE` está vacío, toma credenciales de Elasticsearch desde `.env`.
- RN-02: Si `PARAMETER_STORE` está definido, toma credenciales desde AWS SSM.
- RN-03: La infraestructura local es opcional para ejecución funcional básica del CRUD.

## 9. Soporte técnico (contratos/endpoints/datos/dependencias/riesgos)
### Contratos y endpoints
- API local: `http://localhost:8000`
- Swagger: `http://localhost:8000/documentacion/swagger/`
- ReDoc: `http://localhost:8000/documentacion/redoc/`

### Datos y configuración
- Archivo único: `osiris/.env`
- Plantilla: `osiris/.env.template`
- Variables críticas: `ELASTICSEARCH_HOST`, `ELASTICSEARCH_PORT`, `PARAMETER_STORE`, `AWS_REGION`.

### Dependencias
- Docker + Docker Compose.
- Red Docker externa `elastic_net`.
- Elasticsearch (local por `infraestructura/docker-compose.yml` o remoto).

### Riesgos
- Dependencia de red externa no precreada para `osiris/docker-compose.yml`.
- Divergencia de comportamiento entre local (sin `PARAMETER_STORE`) y remoto (con `PARAMETER_STORE`) por dependencia de AWS SSM.

## 10. Criterios de aceptación verificables
- [ ] `./run_crud.sh` levanta `osiris_back` y expone puerto `8000`.
- [ ] `./infraestructura/run_infra.sh` crea `elastic_net` si no existe y levanta servicios esperados.
- [ ] Documentación describe escenario de solo CRUD sin infraestructura local.

## 11. Evidencia
- `run_crud.sh`
- `infraestructura/run_infra.sh`
- `osiris/docker-compose.yml`
- `infraestructura/docker-compose.yml`
- `osiris/.env.template`
- `README.md`

## 12. Clasificación SDD
- Tipo: AS-IS
- Tamaño relativo: S
- Prioridad: Alta
