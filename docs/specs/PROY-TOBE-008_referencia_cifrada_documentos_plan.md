# Plan de PROY-TOBE-008

## Referencia

Spec `PROY-TOBE-008_referencia_cifrada_documentos.md`, base `f51497c`, autorizada
por solicitud explícita del 2026-11-11 e implementada en el checkout local.

## Enfoque técnico

Agregar serializers y dos APIViews en `apps/campos`. Las utilidades cifrarán JSON
canónico con una clave Fernet y validarán directamente en Elasticsearch la cadena
de padres y el campo `hash`. El GET usará `urllib3` contra la URL fija del Gestor
y un archivo temporal con spool para limitar memoria y resolver errores upstream
antes de responder al cliente.

## Impactos

| Área | Archivo | Cambio | Riesgo |
|---|---|---|---|
| Contrato | `apps/campos/urls.py`, `serializers.py` | dos operaciones | Gateway/rutas |
| Seguridad | `apps/campos/documentos.py` | cifrado y validación ES | datos legados |
| Proxy | `apps/campos/views.py` | Bearer sintáctico, spool, passthrough y errores | contrato Gestor no versionado |
| Configuración | `settings.py`, `.env.template`, `requirements.txt` | clave, URL, límites, Fernet | secreto de despliegue |
| Pruebas/docs | tests, OpenAPI y SDD | evidencia | sin ES/MID real |

## Datos y contrato

No hay migración ni cambio de mapping. Rollback: retirar primero el cliente y
luego los endpoints; las referencias son efímeras y no se persisten. El despliegue
debe configurar una clave dedicada estable en todas las réplicas.

## Estrategia de pruebas

Pruebas puras de cifrado y APITestCase con cliente Elasticsearch y Gestor
mockeados cubren éxito, manipulación, expiración, cruce de contexto, archivo
eliminado, Bearer ausente, upstream y ausencia de llamada remota en rechazos. No
constituyen una prueba end-to-end.

## Despliegue y reversión

Desplegar CRUD y configuración antes del cliente. Rotar la clave requiere aceptar
temporalmente claves anteriores; esta primera versión usa una clave activa única,
por lo que una rotación invalida referencias de máximo 7 días.

## Dudas bloqueantes

Ninguna para el alcance implementado. La ausencia de autenticador/ACL propio, la
transferencia de referencias durante el TTL y el acceso directo al Gestor con una
credencial amplia quedan como riesgos explícitos no resueltos por el cifrado.
