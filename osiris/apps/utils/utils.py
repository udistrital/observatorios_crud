import pandas as pd 

class ProcesadorRecursos():
    
    VALIDADORES = [] 

    datos_validadores = {
    }

    #funcion para enviar los key a datos_validadores desde cero
    def inicializar_datos_validadores(self, **kwargs):
         self.datos_validadores = kwargs


    def agregar_data_validadores(self, **kwargs):
        self.datos_validadores.update(kwargs)


    def ejecutar_validadores(self, dataframe):
        
        for validador in self.VALIDADORES:
            validador.setup(**self.datos_validadores)
            try:
                validador.handle(dataframe)
            except Exception as e:
               return str(e)  

    
    def procesar_csv(self, archivo) -> dict:
            
            df = pd.read_csv(archivo, encoding='latin-1')
            data = df.to_dict(orient='records' )
            errors = self.ejecutar_validadores(df)
            
            return data, errors


    def procesar_json(self, archivo) -> dict:
            
            df = pd.DataFrame(archivo)
            data = df.to_dict(orient='records')
            errors = self.ejecutar_validadores(df)

            return data, errors
