import pandas as pd

def load_excel_data(file_path: str) -> dict:
    """
    Carga y estructura los datos desde un archivo Excel de Micron.
    Devuelve un diccionario con todas las hojas relevantes como DataFrames.
    """
    xls = pd.ExcelFile(file_path)

    data = {}

    for sheet in xls.sheet_names:
        data[sheet] = xls.parse(sheet, header=0)

    return data
