class EstructuraCamposModelo:
    @staticmethod
    def obtener(cliente, estructura_id):
        respuesta = cliente.get(
            index=estructura_id,
            id=estructura_id
        )

        return respuesta["_source"]

    @staticmethod
    def guardar(cliente, estructura_id, estructura):
        cliente.index(
            index=estructura_id,
            id=estructura_id,
            document=estructura,
            refresh=True
        )

        return estructura

    @staticmethod
    def actualizar(cliente, estructura_id, datos):
        estructura = EstructuraCamposModelo.obtener(
            cliente,
            estructura_id
        )

        estructura_actualizada = {
            **estructura,
            **datos,
            "id": estructura_id,
        }

        EstructuraCamposModelo.guardar(
            cliente,
            estructura_id,
            estructura_actualizada
        )

        return estructura_actualizada

    @staticmethod
    def existe(cliente, estructura_id):
        return cliente.indices.exists(index=estructura_id)
