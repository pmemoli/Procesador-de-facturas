from PyPDF2 import PdfReader
import pandas as pd
import numpy as np
import re
import os
import matplotlib.pyplot as plt
from joblib import load
import re
import pandas as pd
from collections import Counter

# Lectura top 500 nombres comunes
top_nombres_df = pd.DataFrame(pd.read_excel('top_names.xlsx'))
top_nombres_df.columns = top_nombres_df.iloc[1]
top_nombres_df = top_nombres_df.drop(top_nombres_df.index[0])
top_nombres_df = top_nombres_df.drop(top_nombres_df.index[1])

top_850_apellidos = '|'.join([r'\b' + re.escape(surname) + r'\b' for surname in top_nombres_df['SURNAME'][:850]])

def common_chars(s1, s2):
    return sum((Counter(s1) & Counter(s2)).values())

# Parsea el invoice de una factura
def invoice_parse(factura_string, path):
    # Patrones ideales
    invoice_keys = ['inv', 'locator', 'num', 'invoice']

    pattern_comp_1 = '(' + '|'.join(re.escape(key) for key in invoice_keys) + ')[: .#]*([a-zA-Z]{0,1}[\d]+?)\n'
    pattern_comp_2 = '(' + '|'.join(re.escape(key) for key in invoice_keys) + ')[: .#]*\n([a-zA-Z]{0,1}[\d]+?)\n'

    invoice_regex_1 = re.findall(pattern_comp_1, factura_string, re.IGNORECASE)
    invoice_regex_2 = re.findall(pattern_comp_2, factura_string, re.IGNORECASE)

    invoice_regex_1 = list(filter(lambda x : 'issued' not in x[1], invoice_regex_1))
    invoice_regex_2 = list(filter(lambda x : 'issued' not in x[1], invoice_regex_2))

    fallo = False
    if invoice_regex_1 != []:
        unparsed_inv = invoice_regex_1[0]
    
    elif invoice_regex_2 != []:
        unparsed_inv = invoice_regex_2[0]
    
    else:
        fallo = True
        
    # Patrones mas irregulares
    simple_pattern = '\n([:#])([a-zA-Z]*\d{8,9})\n'
    last_resort_1 = '\n([a-zA-Z]*\d{8,9})\n'
    last_resort_2 = '\n(.*?)([a-zA-Z]*\d{7,9})\n'

    simple_regex = re.findall(simple_pattern, factura_string, re.IGNORECASE)
    last_resort_regex_1 = re.findall(last_resort_1, factura_string, re.IGNORECASE)
    last_resort_regex_2 = re.findall(last_resort_2, factura_string, re.IGNORECASE)

    if fallo:
        simple_regex = re.findall(simple_pattern, factura_string, re.IGNORECASE)
        if simple_regex != []:
            unparsed_inv = simple_regex[0]

        elif last_resort_regex_1 != []:
            unparsed_inv = last_resort_regex_1[0]
        
        else:
            if last_resort_regex_2 != []:
                unparsed_inv = last_resort_regex_2[0]
            else:
                unparsed_inv = ''

    # Se guarda el resultado a invoice
    if len(unparsed_inv) == 2:
        invoice = unparsed_inv[1].replace(' ', '').replace(':', '')
    else:
        invoice = unparsed_inv

    # Evaluacion final
    nombre_path = path.replace('.pdf', '')
    casi_igual_al_path = len(nombre_path) == len(invoice) and len(invoice) - common_chars(nombre_path, invoice) <= 2
    errado_seguro = len(invoice) < 5 or len(invoice) > 10
    
    if casi_igual_al_path or errado_seguro:
        invoice = nombre_path

    return invoice

# Parsea el costo total de una factura
def costo_total_parse(factura_string):
    total_regex = re.findall(r'Total:[ ]*\$[.,\d]+', factura_string, re.IGNORECASE)
    if total_regex == []:
        total_regex = re.findall(r'Total:[ ]*-\$[.,\d]+', factura_string, re.IGNORECASE)

    costo_total = total_regex[0].replace('Total:', '').replace(',', '').replace('$', '').replace(' ', '')

    if (costo_total[2] == '.'):
        costo_total = costo_total.replace('.', '', 1)

    costo_total = float(costo_total)

    return costo_total

# Parsea el costo profesional de una factura
def costo_prof_parse(factura_string):    
   # Obtiene las filas
    filas = [['items', 'horas', 'precio_por_hora', 'total']]

    texto_relevante = factura_string[factura_string.index('Total') + 5:]
    texto_relevante = '\n' + texto_relevante

    # Regex para distintos casos de filas
    matches_limpios = re.findall(r"\n((?:[ a-zA-Z-].+\n){1,2})([ \d.]+)\n\$([ \d,.]+)\n\$([ \d,.]+)", texto_relevante)
    matches_cero_unico = re.findall(r"\n(0\n)([ \d,.]+)\n\$([ \d,.]+)\n\$([ \d,.]+)", texto_relevante)
    matches_cero_concat = re.findall(r"\n(0 -.+\n)([ \d,.]+)\n\$([ \d,.]+)\n\$([ \d,.]+)", texto_relevante)

    # Append a filas para caso con hora
    matches_limpios.extend(matches_cero_concat)
    matches_limpios.extend(matches_cero_unico)
    for match in matches_limpios:
        fila = []
        fila.append(match[0])
        fila.append(float(match[1].replace(',', '')))
        fila.append(float(match[2].replace(',', '')))
        fila.append(float(match[3].replace(',', '')))

        filas.append(fila)

    df = pd.DataFrame(filas)
    df.columns = df.iloc[0]
    df = df.drop(df.index[0])

    # Obtiene el costo de servicios de profesionales
    # Evalua cuales filas se corresponden a trabajos profesionales
    profesiones = [
        'Engineer', 'Scheduler', 'Manager', 'Principal', 'Designer', 'Specialist',
        'Administrative', 'Supervisor', 'Associate', 'Drafter', 'Consultant', 'Director',
        'Analyst'
    ]

    profesiones_regex = '|'.join(profesiones)

    anti_profs = [
        'Client', 'Expense', 'Meal', 'Equipment', 'Admin Fees'
    ]

    anti_profs_regex = '|'.join([r'\b' + re.escape(anti_prof) + r'\b' for anti_prof in anti_profs])

    contiene_apellido_comun = df['items'].str.contains(top_850_apellidos, case=False, na=False)
    contiene_profesion = df['items'].str.contains(profesiones_regex, case=False, na=False)
    horas_no_default = (df['horas'] != 1.0) & ((df['precio_por_hora'] - df['total']).abs() > 5)
    no_tiene_antiprof = ~df['items'].str.contains(anti_profs_regex, case=False, na=False)

    rows_prof = df[(contiene_apellido_comun | contiene_profesion | horas_no_default) & no_tiene_antiprof]

    costo_prof = sum(rows_prof['total'])

    return costo_prof

# Parsea una factura individual
def parseo_factura(nombre):
    reader = PdfReader(f'model_images/{nombre}')
    string_parse = '\n' + '\n'.join(list(map(lambda x:x.extract_text(), reader.pages)))

    # Invoice
    invoice = invoice_parse(string_parse, nombre)
    print(f'Invoice: {invoice}')

    # Obtiene el costo total
    costo_total = costo_total_parse(string_parse)
    print(f'Costo Total: {costo_total}')

    # Obtiene el costo de profesionales
    costo_prof = costo_prof_parse(string_parse)
    print(f'Costo Profesional: {costo_prof}')

    return [invoice, costo_prof, costo_total]

# Parsea los invoices y los manda a un dataframe
def parse_all(nombre):
    datos_parseados = {
        'path': [],
        'invoice': [],
        'costo_prof': [],
        'costo_total': []
    }

    archivos = os.listdir('model_images')
    datos_parseados['path'] = archivos

    errores = 0
    for archivo in archivos:
        print(f'\nParseando {archivo}...\n')
        try:
            invoice, costo_prof, costo_total = parseo_factura(archivo)
            datos_parseados['invoice'].append(invoice)
            datos_parseados['costo_prof'].append(costo_prof)
            datos_parseados['costo_total'].append(costo_total)

        except:
            print(archivo)
            errores += 1

    print(f'Hubo {errores} errores')

    df_parsed = pd.DataFrame(datos_parseados)

    df_parsed.to_csv(f'{nombre}.csv')

parse_all('modelo_df')