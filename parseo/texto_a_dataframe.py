from joblib import load
import re
import pandas as pd
from collections import Counter
import os
import warnings
from pandas.core.common import SettingWithCopyWarning

warnings.simplefilter(action="ignore", category=SettingWithCopyWarning)

# Lectura top 500 nombres comunes
top_nombres_df = pd.DataFrame(pd.read_excel('top_names.xlsx'))
top_nombres_df.columns = top_nombres_df.iloc[1]
top_nombres_df = top_nombres_df.drop(top_nombres_df.index[0])
top_nombres_df = top_nombres_df.drop(top_nombres_df.index[1])

top_850_apellidos = '|'.join([r'\b' + re.escape(surname) + r'\b' for surname in top_nombres_df['SURNAME'][:850]])

def completar_entero(str):
    try:
        limpiado_facil = float(str)
        return limpiado_facil
    except:
        pass

    cleaned_s = re.sub("[^0-9]", "", str)
    if cleaned_s == '':
        return 1
    
    return float(cleaned_s)

def completar_float(str, remove_first=True, allow_neg=True):
    if remove_first:
        str = str[1:]
    
    if allow_neg:
        cleaned_s = re.sub("[^0-9.,-]", "", str)
    else:
        cleaned_s = re.sub("[^0-9.,]", "", str)

    parts = re.split(r'[.,]', cleaned_s)

    # Evalua si la ultima parte es decimal
    if len(parts[-1]) == 2 or len(parts[-1]) == 1:  
        decimal = parts.pop(-1)
    else:
        decimal = None
    
    # El resto de partes representa miles con maybe excepcion del primero
    whole = "".join(parts)

    if whole == '': # Estaba cortado
        return float(re.sub("[,.]", "", cleaned_s))

    number = float(whole)

    if decimal is not None:
        number += float(decimal) / 100

    return number

# Parsea el invoice de una factura
def invoice_parse(factura_string, path):
    # Patrones ideales
    invoice_keys = ['inv', 'cator', 'num', 'oice']

    pattern_comp_1 = '(' + '|'.join(re.escape(key) for key in invoice_keys) + ')[: .#]*([a-zA-Z]{0,1}[\d]+).{0,1}\n'
    pattern_comp_2 = '\n([:# ])([a-zA-Z]{0,1}\d{6,9}).{0,1}\n'

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
    last_resort_1 = '\n([a-zA-Z]{0,1}\d{6,9}).{0,1}\n'
    last_resort_2 = '\n(.*?)([a-zA-Z]{0,1}\d{6,9}).{0,1}\n'

    last_resort_regex_1 = re.findall(last_resort_1, factura_string, re.IGNORECASE)
    last_resort_regex_2 = re.findall(last_resort_2, factura_string, re.IGNORECASE)

    if fallo:
        if last_resort_regex_1 != []:
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
    def common_chars(s1, s2):
        return sum((Counter(s1) & Counter(s2)).values())

    nombre_path = path.replace('.pdf', '')
    casi_igual_al_path = len(nombre_path) == len(invoice) and len(invoice) - common_chars(nombre_path, invoice) <= 2
    errado_seguro = len(invoice) < 6 or len(invoice) > 10
    
    if casi_igual_al_path or errado_seguro:
        if re.findall('[a-zA-Z]*\d{6,9}', nombre_path) != [] or invoice == '':
            invoice = nombre_path
        # else:
        #     print(invoice, nombre_path)

    return invoice

# Parsea el costo total de una factura
def costo_total_parse(factura_string):
    total_regex = re.findall(r'Total[: -]*\$[.,\d]+', factura_string, re.IGNORECASE)

    # Se encontro correctamente el total
    if len(total_regex) != 0: 
        costo_total = float(completar_float(total_regex[0], remove_first=False))

    # No se encontro el total, defaultea a -1
    else:
        costo_total = -1

    return costo_total

# Parsea el costo profesional de una factura
def costo_prof_parse(factura_string):    
    # Obtiene las filas
    filas = [['items', 'horas', 'precio_por_hora', 'total']]

    texto_relevante = factura_string

    # Regex para filas que no tienen nada especial
    matches_limpios = re.findall(r"\n((?:[ a-zA-Z-].+\n){1,2})([\d.]+)\n([$S5][\d,.]*\d[\d,.]*)\n([$S5][\d,.]*\d[\d,.]*)", texto_relevante)
    matches_sin_horas = re.findall(r"\n((?:[ a-zA-Z-].+\n){1,2})([$S5][\d,.]*\d[\d,.]*)\n([$S5][\d,.]*\d[\d,.]*)", texto_relevante)
    matches_sin_por_hora = re.findall(r"\n((?:[ a-zA-Z-].+\n){1,2})([\d.]+)\n([\d,.]*\d[\d,.]*)\n([$S5][\d,.]*\d[\d,.]*)", texto_relevante)

    # Regex para filas complicadas
    matches_hora_shifted = re.findall(r"\n((?:[ a-zA-Z-].+\n){1,2})([$S5][\d,.]*\d[\d,.]*)\n([\d,.]+)\n([$S5][\d,.]*\d[\d,.]*)", texto_relevante)
    matches_cero_unico = re.findall(r"\n(0\n)([\d,.]+)\n([$S5][\d,.]*\d[\d,.]*)\n([$S5][\d,.]*\d[\d,.]*)", texto_relevante)
    matches_cero_concat = re.findall(r"\n(0 -.+\n)([\d,.]+)\n([$S5][\d,.]*\d[\d,.]*)\n([$S5][\d,.]*\d[\d,.]*)", texto_relevante)
    matches_cero_concat_sin_horas = re.findall(r"\n(0 -.+\n)\n([$S5][\d,.]*\d[\d,.]*)\n([$S5][\d,.]*\d[\d,.]*)", texto_relevante)

    # Append a filas para caso con hora
    matches_limpios.extend(matches_cero_concat)
    matches_limpios.extend(matches_cero_unico)
    for match in matches_limpios:
        fila = []
        fila.append(match[0])
        fila.append(float(completar_entero(match[1])))
        fila.append(float(completar_float(match[2])))
        fila.append(float(completar_float(match[3])))

        filas.append(fila)

    # Appens al caso especial sin hora
    for match in matches_sin_por_hora:
        fila = []
        fila.append(match[0])
        fila.append(float(completar_entero(match[1])))
        fila.append(float(completar_float(match[2], remove_first=False, allow_neg=False)))
        fila.append(float(completar_float(match[3])))

        filas.append(fila)

    # Append a filas para caso sin hora
    matches_sin_horas.extend(matches_cero_concat_sin_horas)
    for match in matches_sin_horas:
        fila = []
        fila.append(match[0])
        fila.append(1)
        fila.append(float(completar_float(match[1])))
        fila.append(float(completar_float(match[2])))

        filas.append(fila)

    # Append al caso shifteado
    for match in matches_hora_shifted:
        fila = []
        fila.append(match[0])
        fila.append(float(completar_entero(match[2])))
        fila.append(float(completar_float(match[1])))
        fila.append(float(completar_float(match[3])))

        filas.append(fila)

    df = pd.DataFrame(filas)
    df.columns = df.iloc[0]
    df = df.drop(df.index[0])

    # Evalua cuales filas se corresponden a trabajos profesionales
    profesiones = [
        'Engineer', 'Scheduler', 'Manager', 'Principal', 'Designer', 'Specialist',
        'Administrative', 'Supervisor', 'Associate', 'Drafter', 'Consultant', 'Director',
        'Analyst', 'Consultant', 'Contractor', 
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

    rows_prof.drop_duplicates(subset=['items', 'total'], keep='first', inplace=True)

    # Calcula finalmente la suma de costo de profesionales
    costo_prof = sum(rows_prof['total'])

    return costo_prof

# Parsea una factura individual
def parseo_factura(raw_parse, path, print_res=False):
    string_parse = '\n'.join(map(lambda x:str(x[1][0]), raw_parse))
    string_parse = '\n' + string_parse

    if print_res:
        print(string_parse)

    # Invoice
    invoice = invoice_parse(string_parse, path)

    # Obtiene el costo total
    try:
        costo_total = costo_total_parse(string_parse)
    except:
        costo_total = -1
    
    # Obtiene el costo de profesionales
    if print_res:
        costo_prof = costo_prof_parse(string_parse)
    else:
        try:
            costo_prof = costo_prof_parse(string_parse)
        except:
            print(path)
            costo_prof = 0

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

    errores = 0
    for i in indices_a_parsear:
        if print_res:
            print(f'\nParseando {pathes[i]}...')

        invoice, costo_prof, costo_total = parseo_factura(raw_parse_strings[i], pathes[i], print_res)
        datos_parseados['invoice'].append(invoice)
        datos_parseados['costo_prof'].append(costo_prof)
        datos_parseados['costo_total'].append(costo_total)
        

    print(f'Hubo {errores} errores\n')

    df_parsed = pd.DataFrame(datos_parseados)

    df_parsed.to_csv(f'dataframes/{nombre_df}.csv')

    if test_paths != None:
        return True
    else:
        return False

# Para testeo
paths_a_testear = ['Incoming_inv_ParaisurZ996560_587.pdf']
subset_paths = [paths_a_testear[0]]
# parse_all('test', 'ocr_img_3800-3899.joblib', subset_paths, print_res=True)

# Corre el parseo para todos los joblist de la carpeta ocr_crudo
ocr_paths = os.listdir('ocr_crudo')
ocr_paths = filter(lambda x : '.joblib' in x, ocr_paths)

for path in ocr_paths:
    finished = parse_all(path, path)#, subset_paths, print_res=True)

    if finished:
        break
