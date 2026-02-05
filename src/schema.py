import pandera as pa
import pandera.pandas as pa_pd # Nova convenção
from pandera.typing import Series
import pandas as pd

# Classe que define o "shape" esperado dos nossos dados
class KabumSchema(pa_pd.DataFrameModel):
    # O nome deve ser string e ter pelo menos 3 caracteres
    nome_produto: Series[str] = pa.Field(str_length={"min_value": 3})
    
    # O preço deve ser float e maior que zero
    preco_pix: Series[float] = pa.Field(gt=0, nullable=True)
    
    # O link deve começar com https://
    link: Series[str] = pa.Field(str_startswith="https://")
    
    # Data de coleta deve ser datetime
    data_coleta: Series[pd.Timestamp]

    class Config:
        # 'coerce' força a conversão de tipos (ex: int -> float)
        coerce = True 
        # 'strict' rejeita colunas que não listamos aqui (limpeza automática)
        strict = True