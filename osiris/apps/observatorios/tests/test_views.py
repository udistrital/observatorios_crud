from .test_setup import TestSetUP
import time
from unittest import mock 
from osiris.settings import ELASTICSEARCH_MAIN_INDEX

class TestViews(TestSetUP):

    def test_crear_observatorio(self):
        response = self.client.post(
            self.observatorios_link,
            self.observatorio_informacion,
            format='multipart'
        )

        # import pdb
        # pdb.set_trace()

        self.assertEqual(
            response.status_code,
            201
        )
  
    def test_actualizar_observatorio(self):
        # Crear un observatorio primero
        with mock.patch('osiris.settings.ELASTICSEARCH_MAIN_INDEX', 'test'):
            response = self.client.post(
                self.observatorios_link,
                self.observatorio_informacion,
                format='multipart'
            )
            observatorio_id = response.data["observatorio_id"]

            # Datos para actualizar el observatorio
            observatorio_actualizado = {
                "nombre": "Nuevo Nombre",
                "descripcion": "Descripción actualizada",
            }

            time.sleep(1)

            response_put = self.client.put(
                f'{self.observatorios_link}{observatorio_id}/',
                observatorio_actualizado,
            )

            time.sleep(1)

            observatorio_data = self.client.get(
                f'{self.observatorios_link}{observatorio_id}/',
            )

            

            self.assertEqual(response_put.status_code, 200)
            self.assertEqual(observatorio_data.data["nombre"], "Nuevo Nombre")
            self.assertEqual(observatorio_data.data["descripcion"], "Descripción actualizada")

