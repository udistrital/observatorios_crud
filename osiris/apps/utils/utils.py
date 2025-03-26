import pandas as pd 

class ProcesadorRecursos():
    
    VALIDADORES = [] 

    def ejecutar_validadores(self, dataframe):
        for validador in self.VALIDADORES:
              validador().handle(dataframe)  

    
    def procesar_csv(self, archivo) -> dict:
            
            df = pd.read_csv(archivo, encoding='latin-1')
            data = df.to_dict(orient='records' )
            self.ejecutar_validadores(df)
            
            return data


    def procesar_json(self, archivo) -> dict:
            
            df = pd.read_json(archivo)
            data = df.to_dict(orient='records')
            self.ejecutar_validadores(df)

            return data


class BaseValidador():
      
      def handle(self, df):
            return df