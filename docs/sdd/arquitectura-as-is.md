# Arquitectura AS-IS

## Referencia y alcance

Documento inspeccionado contra `f51497c` y la implementación local de
`PROY-TOBE-008` el 2026-11-12. No declara conformidad con ISO/IEC/IEEE 42010 ni con C4; usa
sus conceptos de interesados, preocupaciones y vistas para organizar evidencia.

## Interesados y preocupaciones

| Interesado | Preocupación comprobable |
|---|---|
| Usuario de Observatorios | Consultar y, según la UI, administrar jerarquía, evidencias y paneles. |
| Desarrollador backend | Preservar rutas, payloads, mappings y referencias denormalizadas. |
| Desarrollador frontend | Conocer códigos, errores, paginación y efectos de cada operación. |
| Operación OATI | Configurar Django, Elasticsearch, SSM, Docker y despliegue. |
| Seguridad | Identificar fronteras, validación, permisos efectivos y exposición de errores. |
| Agente de código | Localizar evidencia antes de redactar un cambio TO-BE. |

## Contexto C4

```mermaid
flowchart LR
    U[Usuario] -->|HTTPS mediante navegador| C[observatorios_cliente]
    C -->|REST JSON, referencias y contenido| B[observatorios_crud]
    C -->|Carga reemplazo y eliminación| G[Gestor Documental]
    B -->|GET fijo con Bearer reenviado| G
    B -->|Consultas e indexación| E[(Elasticsearch)]
    B -->|Parámetros remotos opcionales| S[AWS SSM]
    M[observatorios_mid legado] -.->|datosArchivo no verificado| B
```

- [VERIFICADO] El cliente consume CRUD para dominio y visualización; consume
  directamente el Gestor solo para carga, reemplazo y eliminación.
- [VERIFICADO] MID concatena `datosArchivo/...` en
  `observatorios_mid/services/observatorios_service.py`.
- [INFERIDO] La integración MID no es operativa con el modelo actual del CRUD.
- [NO VERIFICADO] Gateway, balanceadores y controles perimetrales no están
  descritos por este checkout.

## Contenedores

```mermaid
flowchart TB
    subgraph API[Contenedor Django]
      URL[osiris.urls]
      DRF[APIView y ViewSet]
      SER[Serializers y validación manual]
      ESU[Modelos descriptor y utilidades Elasticsearch]
      PRE[Conversor temporal LibreOffice]
      DOC[Referencia Fernet y proxy documental]
      URL --> DRF --> SER --> ESU
      DRF --> PRE
      DRF --> DOC
    end
    ESU --> ES[(Elasticsearch)]
    PRE --> TMP[(Directorio temporal)]
    DOC --> TMP
    DOC --> GD[Gestor Documental]
    CFG[Entorno o AWS SSM] --> API
```

| Contenedor/componente | Responsabilidad | Evidencia |
|---|---|---|
| Enrutamiento Django | Prefijo dinámico, health y documentación | `osiris/osiris/urls.py` |
| Views DRF | Orquestación, validación adicional, efectos entre índices | `osiris/apps/*/views.py` |
| Serializers | Forma y validación parcial de entradas | `osiris/apps/*/serializers.py` |
| Modelos/utilidades ES | Mappings, consultas e indexación | `osiris/apps/elasticsearch_utils/`; `osiris/apps/*/models.py` |
| Conversión Office | Valida Word/Excel, ejecuta LibreOffice y retorna PDF temporal | `osiris/apps/campos/views.py: VistaPreviaDocumentoView` |
| Proxy documental | Emite/descifra referencias, revalida ES, limita y transmite JSON del Gestor | `osiris/apps/campos/documentos.py`; `ReferenciaDocumentoView`; `ContenidoDocumentoView` |
| SQLite | Soporte interno de Django | `osiris/osiris/settings.py: DATABASES` |

## Límites de confianza

1. Navegador a API: [VERIFICADO] el frontend adjunta Bearer, pero el CRUD no lo
   valida globalmente.
2. API a Elasticsearch: [VERIFICADO] usa credenciales; una construcción del
   cliente desactiva verificación de certificados.
3. API a LibreOffice: [VERIFICADO] archivos no confiables se validan antes de
   conversión y los temporales se eliminan; el semáforo es local al proceso.
4. Entorno a aplicación: [VERIFICADO] configuración local o AWS SSM; no se
   documentan valores secretos.
5. API a Gestor: [VERIFICADO] destino fijo, HTTPS por defecto, TLS verificado y
   Bearer reenviado. El CRUD solo valida su sintaxis; no valida JWT ni ACL por
   proceso, y el Gestor conserva la decisión de autorización.

## Secuencia de jerarquía

```mermaid
sequenceDiagram
    actor UI as observatorios_cliente
    participant V as ViewSet
    participant P as Índice padre
    participant H as Índice hijo
    UI->>V: POST recurso hijo
    V->>P: comprobar padre
    V->>H: crear documento
    V->>P: agregar referencia del hijo
    alt ambas operaciones terminan
      V-->>UI: 201 JSON
    else falla actualización del padre
      V-->>UI: error o compensación específica
    end
```

[VERIFICADO] No hay una transacción común. Factores intentan compensar la creación;
otras capacidades pueden dejar referencias parciales.

## Secuencia documental activa

```mermaid
sequenceDiagram
    actor U as Usuario
    participant C as observatorios_cliente
    participant G as Gestor Documental
    participant B as observatorios_crud
    participant E as Elasticsearch
    U->>C: selecciona archivo y metadatos
    C->>G: POST document/uploadAnyFormat
    G-->>C: Enlace o hash
    C->>B: POST campos/datos/{estructura}/
    B->>E: actualiza data embebida
    E-->>B: resultado
    B-->>C: 201 registro
```

[VERIFICADO] El CRUD no guarda el binario en este flujo. [INFERIDO] si la segunda
escritura falla, el archivo puede quedar huérfano.

## Secuencia de visualización activa

```mermaid
sequenceDiagram
    actor U as Usuario
    participant C as observatorios_cliente
    participant B as observatorios_crud
    participant E as Elasticsearch
    participant G as Gestor Documental
    U->>C: abrir documento
    C->>B: POST campos/documentos/referencias/ + contexto + Bearer
    B->>E: validar cadena activa y coincidencia hash única
    E-->>B: asociación vigente
    B-->>C: 200 {referencia: v1_...}
    C->>C: abrir /documentos/{referencia}
    C->>B: GET campos/documentos/{referencia}/ + Bearer
    B->>B: descifrar con TTL
    B->>E: revalidar cadena y asociación
    B->>G: GET document/{documento_id} + Bearer
    G-->>B: JSON
    B->>B: validar y completar spool temporal
    B-->>C: 200 JSON, no-store/no-cache/nosniff
```

[VERIFICADO] No hay consulta directa del visor activo al Gestor ni intervención
del MID. El POST y el GET solo comprueban sintaxis Bearer. La referencia es
transferible entre sesiones autenticadas durante el TTL y una credencial de
alcance amplio conserva acceso directo al Gestor como riesgo residual.

## Decisiones observadas y limitaciones

- [VERIFICADO] Datos de dominio en Elasticsearch, con índices fijos y dinámicos.
- [VERIFICADO] Relaciones jerárquicas denormalizadas en padre e hijo.
- [VERIFICADO] Registros de estructura embebidos en un único documento.
- [VERIFICADO] Rutas versionadas mediante segmento libre, no mediante routers por
  versión.
- [VERIFICADO] Errores y borrados heterogéneos por capacidad.
- [VERIFICADO] El proxy usa un `SpooledTemporaryFile`; después del umbral de
  memoria usa disco temporal y resuelve límites/errores upstream antes del 200.
- [NO VERIFICADO] No existen ADR que demuestren por qué se eligieron estas
  decisiones; no deben reinterpretarse como recomendaciones TO-BE.

## Correspondencias

- Rutas y operaciones: [`../api/openapi.yaml`](../api/openapi.yaml).
- Datos y mappings: [`../data/modelo-e-indices.md`](../data/modelo-e-indices.md).
- Integraciones: [`matriz_interacciones.md`](matriz_interacciones.md).
- Riesgos: [`brechas-y-riesgos.md`](brechas-y-riesgos.md).
- Operación: [`../operations/ejecucion-y-despliegue.md`](../operations/ejecucion-y-despliegue.md).
