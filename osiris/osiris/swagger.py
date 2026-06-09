from collections import OrderedDict

from drf_yasg.generators import OpenAPISchemaGenerator
from drf_yasg import openapi


class AtlasSchemaGenerator(OpenAPISchemaGenerator):
    ignored_tag_segments = {"api"}
    tag_aliases = {
        "constructor_graficos": "Graficos",
        "datosArchivo": "Datos Archivo",
    }

    def get_operation_keys(self, subpath, method, view):
        operation_keys = super().get_operation_keys(subpath, method, view)
        normalized_keys = [
            key for key in operation_keys
            if key not in self.ignored_tag_segments and not key.startswith("{")
        ]

        if not normalized_keys:
            return operation_keys

        normalized_keys[0] = self.tag_aliases.get(
            normalized_keys[0],
            normalized_keys[0].replace("_", " ").replace("-", " ").title(),
        )
        return normalized_keys


class AtlasWso2SchemaGenerator(AtlasSchemaGenerator):
    wso2_managed_prefix = "/api/{version}"

    def get_paths(self, endpoints, components, request, public):
        if not endpoints:
            return openapi.Paths(paths={}), ""

        paths = OrderedDict()
        for path, (view_cls, methods) in sorted(endpoints.items()):
            operations = {}
            for method, view in methods:
                if not self.should_include_endpoint(path, method, view, public):
                    continue

                operation = self.get_operation(view, path, "", method, components, request)
                if operation is not None:
                    operations[method.lower()] = operation

            if operations:
                exposed_path = self.strip_wso2_managed_prefix(path)
                paths[exposed_path] = self.get_path_item(exposed_path, view_cls, operations)

        return self.get_paths_object(paths), ""

    def strip_wso2_managed_prefix(self, path):
        if not path.startswith(self.wso2_managed_prefix):
            return path

        exposed_path = path[len(self.wso2_managed_prefix):]
        return exposed_path if exposed_path.startswith("/") else f"/{exposed_path}"
