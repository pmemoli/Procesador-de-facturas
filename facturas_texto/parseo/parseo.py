from PyPDF2 import PdfReader
import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
from joblib import load
import re
import pandas as pd
import warnings
from pandas.core.common import SettingWithCopyWarning
from .modulos.invoice_parse import *
from .modulos.costo_total_parse import *
from .modulos.costo_prof_parse import *

warnings.simplefilter(action="ignore", category=SettingWithCopyWarning)

'''
El parseo se lleva a cabo por la funcion parse_all(nombre_dataframe). El programa convierte
todas las imagenes en model_images a texto y luego de parsearlas las guarda en un dataframe
en la carpeta de modelo.

parse_all() llama a parseo_factura(nombre_factura) que convierte a una imagen individual
en una tripla de {invoice, costo total, costo profesional}. Cada objeto se parsea por
las funciones de invoice_parse(), costo_total_parse() y parseo_factura() respectivamente.
Cada funcion se almacena en la carpeta de modulos por su extension.
'''

# Parsea una factura individual
def parseo_factura(nombre_factura, print_res=False):
    reader = PdfReader(f'facturas/{nombre_factura}')
    string_parse = '\n' + '\n'.join(list(map(lambda x:x.extract_text(), reader.pages)))

    # Invoice
    invoice = invoice_parse(string_parse, nombre_factura)

    # Obtiene el costo total
    costo_total = costo_total_parse(string_parse)

    # Obtiene el costo de profesionales
    costo_prof = costo_prof_parse(string_parse)

    if print_res:
        print(f'Invoice: {invoice}')
        print(f'Costo Total: {costo_total}')
        print(f'Costo Profesional: {costo_prof}')

    return [invoice, costo_prof, costo_total]

# Parsea los invoices y los manda a un dataframe
def parse_all(nombre_dataframe):
    datos_parseados = {
        'path': [],
        'invoice': [],
        'costo_prof': [],
        'costo_total': []
    }

    archivos = os.listdir('images')
    datos_parseados['path'] = archivos

    # Itera sobre cada factura y la parsea. Se guardan los resultados en el dataframe
    for archivo in archivos:
        print(f'\nParseando {archivo}...\n')

        invoice, costo_prof, costo_total = parseo_factura(archivo)
        datos_parseados['invoice'].append(invoice)
        datos_parseados['costo_prof'].append(costo_prof)
        datos_parseados['costo_total'].append(costo_total)

    df_parsed = pd.DataFrame(datos_parseados)

    df_parsed.to_csv(f'../modelo/{nombre_dataframe}.csv')

parse_all('modelo_df')
