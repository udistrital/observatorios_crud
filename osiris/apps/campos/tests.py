import io
import subprocess
import tempfile
import zipfile
from pathlib import Path
from unittest.mock import patch

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.estructuras.serializers import CampoEstructuraSerializer

from .utils import (
    LONGITUD_MAXIMA_ENLACE,
    TIPOS_CAMPOS_PERMITIDOS,
    aplicar_migraciones_data,
    construir_valores_registro,
    convertir_valor_por_tipo,
    normalizar_campos_con_ids,
    obtener_mapping_tipo_campo,
    obtener_tipos_campos,
)
from .views import ErrorVistaPrevia, FIRMA_OLE


class TipoCampoEnlaceTests(SimpleTestCase):
    def test_expone_enlace_en_catalogo_y_validadores(self):
        self.assertIn("link", TIPOS_CAMPOS_PERMITIDOS)
        self.assertIn(
            {"label": "Enlace", "value": "link"},
            obtener_tipos_campos(),
        )

        serializer = CampoEstructuraSerializer(
            data={"nombre_campo": "Sitio web", "tipo_campo": "link"}
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_mapea_enlace_como_keyword(self):
        self.assertEqual(
            obtener_mapping_tipo_campo("link"),
            {"type": "keyword"},
        )

    def test_convierte_enlaces_http_y_https(self):
        for enlace in (
            "http://example.org",
            "http://intranet",
            "http://[::1]",
            "https://münich.example",
            "https://example.org/ruta?consulta=1#seccion",
        ):
            with self.subTest(enlace=enlace):
                self.assertEqual(
                    convertir_valor_por_tipo(f"  {enlace}  ", "link"),
                    enlace,
                )

        self.assertIsNone(convertir_valor_por_tipo("", "link"))
        self.assertIsNone(convertir_valor_por_tipo("   ", "link"))

    def test_rechaza_enlaces_invalidos_o_no_permitidos(self):
        for enlace in (
            "example.org",
            "javascript:alert(1)",
            "data:text/html,contenido",
            "ftp://example.org/archivo",
            "https://",
            "https://example.org/ruta con espacios",
            "https://example.org\\@otro.example",
            "https://example.org:99999",
            "http:example.org",
            "http:///example.org",
            "http://example.org:0",
            "http://exa%mple.org",
            "http://%65xample.org",
            "http://256.256.256.256",
            "http://[v1.test]",
        ):
            with self.subTest(enlace=enlace):
                with self.assertRaisesRegex(
                    ValueError,
                    "esquema http:// o https://",
                ):
                    convertir_valor_por_tipo(enlace, "link")

    def test_rechaza_enlace_demasiado_largo(self):
        enlace = "https://example.org/" + (
            "a" * LONGITUD_MAXIMA_ENLACE
        )

        with self.assertRaisesRegex(ValueError, "2048 caracteres"):
            convertir_valor_por_tipo(enlace, "link")

    def test_asocia_error_de_enlace_con_nombre_de_campo(self):
        campos = [
            {
                "campo_id": "campo_enlace",
                "nombre_campo": "Sitio web",
                "tipo_campo": "link",
                "activo": True,
            }
        ]

        with self.assertRaises(ValueError) as contexto:
            construir_valores_registro(
                campos,
                {"Sitio web": "javascript:alert(1)"},
            )

        self.assertEqual(
            contexto.exception.args[0],
            {
                "Sitio web": (
                    "Debe ser una URL válida con esquema http:// o https://."
                )
            },
        )

    @patch("apps.campos.utils.generar_campo_id", return_value="campo_nuevo")
    def test_migra_enlace_desde_registro_plano_legado(self, _generar_id):
        campos, migraciones = normalizar_campos_con_ids(
            [
                {
                    "campo_id": "campo_anterior",
                    "nombre_campo": "Sitio web",
                    "tipo_campo": "link",
                    "migrar_data": True,
                }
            ],
            [
                {
                    "campo_id": "campo_anterior",
                    "nombre_campo": "Sitio web",
                    "tipo_campo": "text",
                }
            ],
        )

        resultado = aplicar_migraciones_data(
            [
                {
                    "Sitio web": "https://example.org/legado",
                    "activo": True,
                }
            ],
            migraciones,
            campos,
        )

        self.assertEqual(
            resultado[0]["valores"]["campo_nuevo"],
            "https://example.org/legado",
        )
        self.assertNotIn("Sitio web", resultado[0])

        resultado_reservado = aplicar_migraciones_data(
            [{"activo": False}],
            [
                {
                    "campo_anterior_id": "campo_anterior",
                    "campo_anterior_nombre": "activo",
                    "campo_nuevo_id": "campo_nuevo",
                    "tipo_nuevo": "link",
                    "migrar_data": True,
                }
            ],
            campos,
        )

        self.assertFalse(resultado_reservado[0]["activo"])
        self.assertIsNone(
            resultado_reservado[0]["valores"]["campo_nuevo"]
        )


@override_settings(
    DOCUMENT_PREVIEW_MAX_BYTES=2 * 1024 * 1024,
    DOCUMENT_PREVIEW_MAX_PDF_BYTES=2 * 1024 * 1024,
    DOCUMENT_PREVIEW_TIMEOUT_SECONDS=5,
    LIBREOFFICE_EXECUTABLE="/usr/bin/libreoffice",
)
class VistaPreviaDocumentoTests(APITestCase):
    MIME_POR_EXTENSION = {
        ".doc": "application/msword",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".xls": "application/vnd.ms-excel",
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    }

    def setUp(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer token-prueba")
        self.url = reverse(
            "vista-previa-documento",
            kwargs={"version": "v1"},
        )

    def crear_ooxml(self, extension):
        contenido = io.BytesIO()
        parte_principal = (
            "word/document.xml"
            if extension == ".docx"
            else "xl/workbook.xml"
        )
        content_type = (
            "application/vnd.openxmlformats-officedocument."
            "wordprocessingml.document.main+xml"
            if extension == ".docx"
            else "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet.main+xml"
        )

        with zipfile.ZipFile(contenido, "w", zipfile.ZIP_DEFLATED) as paquete:
            paquete.writestr(
                "[Content_Types].xml",
                '<Types xmlns="http://schemas.openxmlformats.org/package/'
                '2006/content-types"><Override PartName="/'
                f'{parte_principal}" ContentType="{content_type}" /></Types>',
            )
            paquete.writestr(parte_principal, "<contenido />")

        return contenido.getvalue()

    def crear_archivo(self, extension, contenido=None, mime=None):
        if contenido is None:
            contenido = (
                self.crear_ooxml(extension)
                if extension in {".docx", ".xlsx"}
                else FIRMA_OLE + b"contenido-office"
            )

        return SimpleUploadedFile(
            f"documento{extension}",
            contenido,
            content_type=mime or self.MIME_POR_EXTENSION.get(extension),
        )

    @patch("apps.campos.views.convertir_documento_office_pdf")
    def test_genera_pdf_inline_para_formatos_ooxml(self, convertir):
        convertir.return_value = b"%PDF-1.4\ncontenido"

        for extension in (".docx", ".xlsx"):
            with self.subTest(extension=extension):
                response = self.client.post(
                    self.url,
                    {"archivo": self.crear_archivo(extension)},
                    format="multipart",
                )

                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertEqual(response["Content-Type"], "application/pdf")
                self.assertEqual(
                    response["Content-Disposition"],
                    'inline; filename="vista-previa.pdf"',
                )
                self.assertEqual(response.content, b"%PDF-1.4\ncontenido")

    def test_rechaza_solicitud_sin_archivo(self):
        response = self.client.post(self.url, {}, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_rechaza_solicitud_sin_token(self):
        self.client.credentials()

        response = self.client.post(
            self.url,
            {"archivo": self.crear_archivo(".docx")},
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response["WWW-Authenticate"], "Bearer")

    def test_rechaza_extension_no_permitida(self):
        response = self.client.post(
            self.url,
            {
                "archivo": SimpleUploadedFile(
                    "archivo.exe",
                    b"contenido",
                    content_type="application/octet-stream",
                )
            },
            format="multipart",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        )

    def test_rechaza_mime_incompatible(self):
        response = self.client.post(
            self.url,
            {
                "archivo": self.crear_archivo(
                    ".docx",
                    mime="application/javascript",
                )
            },
            format="multipart",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        )

    def test_rechaza_contenido_incompatible(self):
        response = self.client.post(
            self.url,
            {"archivo": self.crear_archivo(".xlsx", contenido=b"no-es-zip")},
            format="multipart",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        )

    @override_settings(DOCUMENT_PREVIEW_MAX_BYTES=10)
    def test_rechaza_archivo_que_supera_limite(self):
        response = self.client.post(
            self.url,
            {"archivo": self.crear_archivo(".doc", contenido=FIRMA_OLE + b"123")},
            format="multipart",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        )

    @patch("apps.campos.views.convertir_documento_office_pdf")
    def test_controla_error_del_conversor(self, convertir):
        convertir.side_effect = ErrorVistaPrevia(
            "No fue posible generar la vista previa del documento.",
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

        response = self.client.post(
            self.url,
            {"archivo": self.crear_archivo(".docx")},
            format="multipart",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        )
        self.assertEqual(response.json()["status"], "error")

    def test_libreoffice_convierte_los_cuatro_formatos_a_pdf(self):
        ejecutable = Path(settings.LIBREOFFICE_EXECUTABLE)

        if not ejecutable.is_file():
            self.skipTest("LibreOffice no esta instalado en este entorno")

        with tempfile.TemporaryDirectory(prefix="preview-fixtures-") as temporal:
            raiz = Path(temporal)

            for extension in self.MIME_POR_EXTENSION:
                with self.subTest(extension=extension):
                    directorio = raiz / extension.lstrip(".")
                    perfil = directorio / "perfil"
                    directorio.mkdir()
                    perfil.mkdir()

                    if extension in {".doc", ".docx"}:
                        fuente = directorio / "documento.fodt"
                        fuente.write_text(
                            '<?xml version="1.0" encoding="UTF-8"?>'
                            '<office:document xmlns:office="urn:oasis:names:tc:'
                            'opendocument:xmlns:office:1.0" '
                            'xmlns:text="urn:oasis:names:tc:opendocument:'
                            'xmlns:text:1.0" office:mimetype="application/'
                            'vnd.oasis.opendocument.text" office:version="1.3">'
                            "<office:body><office:text><text:p>Vista previa Word "
                            "con contenido verificable.</text:p></office:text>"
                            "</office:body></office:document>",
                            encoding="utf-8",
                        )
                    else:
                        fuente = directorio / "documento.csv"
                        fuente.write_text(
                            "columna,valor\nVista previa Excel,42\n",
                            encoding="utf-8",
                        )

                    resultado = subprocess.run(
                        [
                            str(ejecutable),
                            "--headless",
                            "--nologo",
                            "--nodefault",
                            "--nolockcheck",
                            "--nofirststartwizard",
                            f"-env:UserInstallation={perfil.resolve().as_uri()}",
                            "--convert-to",
                            extension.lstrip("."),
                            "--outdir",
                            str(directorio),
                            str(fuente),
                        ],
                        check=True,
                        capture_output=True,
                        timeout=20,
                    )

                    office = directorio / f"documento{extension}"
                    self.assertTrue(
                        office.is_file(),
                        msg=(
                            f"stdout={resultado.stdout!r}, stderr={resultado.stderr!r}, "
                            f"archivos={[ruta.name for ruta in directorio.iterdir()]}"
                        ),
                    )

                    response = self.client.post(
                        self.url,
                        {
                            "archivo": self.crear_archivo(
                                extension,
                                contenido=office.read_bytes(),
                            )
                        },
                        format="multipart",
                    )

                    self.assertEqual(response.status_code, status.HTTP_200_OK)
                    self.assertEqual(response["Content-Type"], "application/pdf")
                    self.assertTrue(response.content.startswith(b"%PDF-"))
                    self.assertIn(b"%%EOF", response.content[-1024:])
