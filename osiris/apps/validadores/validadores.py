class BaseValidador():
      
    def __init_subclass__(cls):
           if not hasattr(cls, 'dependencias_requeridas'):
               raise NotImplementedError("La clase hija debe definir 'dependencias_requeridas' asi sea como un diccionario vacio")

    def setup(self, *args, **kwargs):
            for item in self.dependencias_requeridas:
                if item not in kwargs:
                    raise ValueError(f"Falta el argumento requerido: {item}")
      
    def handle(self, df):
            return df