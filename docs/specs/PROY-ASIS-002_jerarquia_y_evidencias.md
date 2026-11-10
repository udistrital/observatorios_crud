# PROY-ASIS-002 Jerarquía y estructuras de evidencia

## Identidad

| Campo | Valor |
|---|---|
| Sistema | `observatorios_crud` |
| Estado | AS-IS |
| Referencia | `3de996b`, 2026-11-10 |
| Evidencia principal | `osiris/apps/{procesos,factores,caracteristicas,aspectos,estructuras}/` |

## Contexto y alcance

**Como** consumidor de la API, **quiero** gestionar la jerarquía proceso, factor,
característica, aspecto y estructura, **para** organizar evidencias.

Incluye CRUD HTTP y referencias denormalizadas. Excluye autorización institucional,
migración de datos, binarios y funcionamiento del cliente.

## Requisitos y reglas

| ID | Requisito AS-IS | Regla asociada |
|---|---|---|
| REQ-JER-001 | Listar y mutar procesos. | BR-JER-001: lista ordenada por `orden,nombre`; DELETE desactiva. |
| REQ-JER-002 | Asociar factor con proceso. | BR-JER-002: se guarda `proceso_id` y referencia en `factores[]`. |
| REQ-JER-003 | Asociar característica con factor. | BR-JER-003: padre debe existir. |
| REQ-JER-004 | Asociar aspecto con característica. | BR-JER-004: `tipo_evidencia` de referencias es Documental o Tabla. |
| REQ-JER-005 | Crear estructura dinámica. | BR-JER-005: índice `atlas_estructura_<tipo>_<uuid>`. |
| REQ-JER-006 | Consultar/mover/desactivar nodos. | BR-JER-006: PUT/PATCH son parciales; actualizaciones padre/hijo son separadas. |

## Escenario principal

Precondición: el padre existe. El consumidor crea el hijo; la vista valida el
serializer, crea el documento y actualiza la referencia del padre. En éxito retorna
201. Si el padre no existe retorna 400 o 404 según la capacidad. Un fallo entre
escrituras puede dejar estado parcial.

## Criterios de aceptación descriptivos

- **AC-JER-001**: Dado un proceso existente, cuando se crea un factor válido,
  entonces el factor conserva `proceso_id` y el proceso referencia su ID.
- **AC-JER-002**: Dado un filtro padre admitido, cuando se lista el hijo, entonces
  la respuesta contiene solo coincidencias hasta el límite del handler.
- **AC-JER-003**: Dado un DELETE válido, cuando termina, entonces el documento se
  marca inactivo y se devuelve el estado específico de la ruta.
- **AC-JER-004**: Dado un fallo de la segunda escritura, entonces no se presupone
  rollback salvo compensación explícita del handler.

## Contratos y NFR

Rutas y respuestas: [`../api/openapi.yaml`](../api/openapi.yaml). [VERIFICADO] No
hay transacción multiíndice ni autorización por objeto. [NO VERIFICADO] Límites de
rendimiento, disponibilidad y concurrencia.

## Pruebas, riesgos y dudas

No se identificaron pruebas ejecutables de estas capacidades. Riesgos: referencias
huérfanas, soft delete sin limpieza y exposición de errores. Ver
[`../sdd/brechas-y-riesgos.md`](../sdd/brechas-y-riesgos.md).
