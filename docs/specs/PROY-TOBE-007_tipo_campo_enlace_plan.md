# Plan de PROY-TOBE-007

## Referencia

Spec `PROY-TOBE-007_tipo_campo_enlace.md`, base `1ad6ef3`, aprobada para esta
entrega. No se agregarán rutas, dependencias ni migraciones SQL.

## Enfoque técnico

Agregar `link` a las listas permitidas, traducirlo explícitamente a mapping
`keyword` y validar sus valores con `urllib.parse` limitado a HTTP(S), host y
puerto válidos. Los rechazos usarán `ValueError` para conservar el contrato 400
de las vistas de registros.

## Impactos

| Área | Archivo/servicio | Cambio previsto | Riesgo |
|---|---|---|---|
| Dominio | `apps/campos/utils.py` | catálogo, mapping y conversión | Divergencia con cliente |
| Contrato inicial | `apps/estructuras/serializers.py` | admitir `link` | Lista duplicada |
| Pruebas | `apps/campos/tests.py` | casos puros sin Elasticsearch | Diferencias de validación del navegador |
| Documentación | OpenAPI, datos, AS-IS y matriz | convergencia | Conteos obsoletos |

## Datos y contrato

No hay migración masiva. Los documentos nuevos conservan `tipo_campo: "link"`
y sus valores se indexan como `keyword`. El rollback de código deja legibles los
documentos, pero no permitiría volver a guardar su definición hasta restaurar el
soporte del tipo.

## Estrategia de pruebas

Cubrir catálogo, serializer, mapping, HTTP/HTTPS, vacío, esquema ausente,
protocolos peligrosos, URL malformada y longitud máxima. Ejecutar suite de campos
y `manage.py check`; una integración real con Elasticsearch queda condicionada a
la disponibilidad local del servicio.

## Despliegue y reversión

Desplegar CRUD antes o junto con el cliente. Revertir primero el cliente para que
no cree campos nuevos y después el CRUD. No se borran ni transforman datos.

## Dudas bloqueantes

Ninguna. Tipo técnico, protocolos, longitud, vacío y compatibilidad quedaron
definidos en la spec.
