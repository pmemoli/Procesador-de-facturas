from joblib import load
import pandas as pd
import os
import modulos.invoice_parse as inv_par
import modulos.costo_total_parse as tot_par
import modulos.costo_prof_parse as prof_par

'''
El parseo se lleva a cabo por la funcion parse_all(nombre_df, nombre_joblib). El programa convierte
el archivo .joblib "nombre_joblib" (almacenado en ./ocr_crudo) a texto. Luego lo almacena
como un dataframe "nombre_df" que tiene columnas de numero de factura, costo total y costo
profesional respectivamente.

parse_all(nombre_df, nombre_joblib) llama a parseo_factura(raw_parse, path) que toma un
elemento de la lista almacenada en el archivo joblib junto con su path. Retorna una tripla
{invoice, costo total, costo profesional} correspondiente a ese elemento. Cada item de la lista
se parsea por las funciones de invoice_parse(), costo_total_parse() y parseo_factura()
respectivamente, donde las funciones se almacenan en la carpeta de modulos por su extension.
'''

# Parsea una factura individual
def parseo_factura(raw_parse, path, print_res=False):
    # Convierte el objeto que retorna paddleOCR a un string continuo separado por newline characters
    string_parse = '\n'.join(map(lambda x:str(x[1][0]), raw_parse))
    string_parse = '\n' + string_parse

    if print_res:
        print(string_parse)

    # Obtiene el numero de factura
    invoice = inv_par.invoice_parse(string_parse, path)

    # Obtiene el costo total
    try:
        costo_total = tot_par.costo_total_parse(string_parse)
    except:
        costo_total = -1
    
    # Obtiene el costo de profesionales
    if print_res:
        costo_prof = prof_par.costo_prof_parse(string_parse)
    else:
        costo_prof = prof_par.costo_prof_parse(string_parse)

    if print_res:
        print(f'\nInvoice: {invoice}')
        print(f'Costo Total: {costo_total}')
        print(f'Costo Profesional: {costo_prof}')

    return [invoice, costo_prof, costo_total]

# Parsea los invoices y los manda a un dataframe
def parse_all(nombre_df, nombre_joblib, test_paths=None, print_res=False):
    print(f'Parseando {nombre_joblib}...')

    datos_parseados = {
        'path': [],
        'invoice': [],
        'costo_prof': [],
        'costo_total': []
    }

    raw_parses = load(f'ocr_crudo/{nombre_joblib}')

    pathes = [obj['path'] for obj in raw_parses]
    raw_parse_strings = [obj['text'] for obj in raw_parses]

    indices_a_parsear = range(len(pathes))

    # Por testeo se permite limitar los documentos trabajados a un subconjunto
    if test_paths != None:
        indices_a_parsear = []
        for i in range(len(pathes)):
            if pathes[i] in test_paths:
                indices_a_parsear.append(i)

        if indices_a_parsear == []:
            return False

        datos_parseados['path'] = test_paths

    else:
        datos_parseados['path'] = pathes

    # Itera sobre cada elemento del objeto joblib
    for i in indices_a_parsear:
        if print_res:
            print(f'\nParseando {pathes[i]}...')

        invoice, costo_prof, costo_total = parseo_factura(raw_parse_strings[i], pathes[i], print_res)
        datos_parseados['invoice'].append(invoice)
        datos_parseados['costo_prof'].append(costo_prof)
        datos_parseados['costo_total'].append(costo_total)
        
    df_parsed = pd.DataFrame(datos_parseados)

    df_parsed.to_csv(f'dataframes/{nombre_df}.csv')

    if test_paths != None:
        return True
    else:
        return False

# Para testeo
# WrightandSons_2022-02-09.pdf, 283339745.pdf, 2023-01-24_2002.pdf
paths_a_testear = ['Incoming_inv_ParaisurZ996560_7156.pdf']
subset_paths = [paths_a_testear[0]]
# parse_all('test', 'ocr_img_4800-4899.joblib', subset_paths, print_res=True)

# Corre el parseo para todos los joblist de la carpeta ocr_crudo
ocr_paths = os.listdir('ocr_crudo')
ocr_paths = filter(lambda x : '.joblib' in x, ocr_paths)

for path in ocr_paths:
    finished = parse_all(path, path)#, subset_paths, print_res=True)

    if finished:
        break
