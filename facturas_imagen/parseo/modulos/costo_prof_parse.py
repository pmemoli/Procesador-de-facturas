import re
import nltk
from fuzzywuzzy import fuzz
import pandas as pd
import warnings
from pandas.core.common import SettingWithCopyWarning

warnings.simplefilter(action="ignore", category=SettingWithCopyWarning)

# Implementa una funcion que evalua si hay una keyword en un string, con la caracteristica
# que usa la distancia de Levinshtein para ver si dos strings son iguales (asi no se pierden datos
# por falta de ortografia)
def fuzzy_contains(text, keywords, score_cutoff=80):
    for keyword in keywords:
        keyword_len = len(keyword)
        text_len = len(text)
        if text_len >= keyword_len:
            text_ngrams = nltk.ngrams(text.lower(), keyword_len)
            text_substrings = [''.join(ngram) for ngram in text_ngrams]
            for substring in text_substrings:
                if fuzz.ratio(substring, keyword.lower()) >= score_cutoff:
                    return True
    return False

# Evalua si un numero es multiplo no identico de otro
def is_multiple_or_division(num1, num2):
    num1 = abs(num1)
    num2 = abs(num2)
    
    if num1 == 0 or num2 == 0:
        return False

    ratio = num1 / num2
    cociente_entero = ratio.is_integer() or (ratio ** (-1)).is_integer()
    if ratio != 1 and cociente_entero:
        return True

    div = num1 / num2
    if div == 2 or div == 0.5:
        return True
    
    return False

# Convierte una fila a negativo si una columna es negativa
def convert_to_same_positivity(row):
    if row['precio_por_hora'] < 0 and row['total'] > 0:
        row['total'] *= -1
    elif row['precio_por_hora'] > 0 and row['total'] < 0:
        row['precio_por_hora'] *= -1
    return row

# Parsea un stirng a un entero
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

# Parsea un string a un float
def completar_float(str, remove_first=True, allow_neg=True):
    constant = 1

    if remove_first:
        if str[0] == '-':
            str = str[2:]
            constant = -1
        else:
            str = str[1:]
    
    if allow_neg:
        cleaned_s = re.sub("[^0-9.,-]", "", str)
    else:
        cleaned_s = re.sub("[^0-9.,]", "", str)

    parts = re.split(r'[.,]', cleaned_s)

    # Si no hay punto hay muchas chances de que este cortado por lo que es mejor perder el dato
    if len(parts) == 1:
        return 0

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

    return number * constant

# Lectura top 850 apellidos mas comunes en estados unidos
top_nombres_df = pd.DataFrame(pd.read_excel('top_names.xlsx'))
top_nombres_df.columns = top_nombres_df.iloc[1]
top_nombres_df = top_nombres_df.drop(top_nombres_df.index[0])
top_nombres_df = top_nombres_df.drop(top_nombres_df.index[1])

top_850_apellidos = '|'.join([r'\b' + re.escape(surname) + r'\b' for surname in top_nombres_df['SURNAME'][:850]])

# Parsea el costo profesional de una factura
def costo_prof_parse(factura_string):    
    # Obtiene las filas
    filas = [['items', 'horas', 'precio_por_hora', 'total']]

    texto_relevante = factura_string

    # Regex para filas que no tienen nada especial
    matches_limpios = re.findall(r"\n((?:0?[ a-zA-Z-].+\n))([\d.]+)\n([-]?[$S5]\d[\d,.]*)\n([-]?[$S5]\d[\d,.]*)", texto_relevante)
    matches_cero = re.findall(r"\n(0[ -]?\n)([\d.]+)\n([-]?[$S5]\d[\d,.]*)\n([-]?[$S5]\d[\d,.]*)", texto_relevante)

    matches_limpios.extend(matches_cero)
    nombres_limpios = [match[0] for match in matches_limpios]

    # Regex para filas complicadas
    matches_hora_shifted = re.findall(r"\n((?:0?[ a-zA-Z-].+\n))([-]?[$S5]\d[\d,.]*)\n([\d,.]+)\n([-]?[$S5]\d[\d,.]*)", texto_relevante)
    matches_sin_horas = re.findall(r"\n((?:0?[ a-zA-Z-].+\n))([-]?[$S5]\d[\d,.]*)\n([-]?[$S5]\d[\d,.]*)", texto_relevante)
    matches_sin_por_hora = re.findall(r"\n((?:0?[ a-zA-Z-].+\n))([\d.]+)\n([\d,.]*\d[\d,.]*)\n([-]?[$S5]\d[\d,.]*)", texto_relevante)

    nombres_sin_por_hora = [match[0] for match in matches_sin_por_hora]
    nombres_sin_horas = [match[0] for match in matches_sin_horas]

    # Append a filas para caso con hora
    for match in matches_limpios:
        fila = []
        fila.append(match[0])
        fila.append(float(completar_entero(match[1])))
        fila.append(float(completar_float(match[2])))
        fila.append(float(completar_float(match[3])))

        filas.append(fila)

    # Appens al caso especial sin costo por hora
    for match in matches_sin_por_hora:
        if match[0] not in nombres_limpios:
            fila = []
            fila.append(match[0])
            fila.append(float(completar_entero(match[1])))
            fila.append(float(completar_float(match[2], remove_first=False, allow_neg=False)))
            fila.append(float(completar_float(match[3])))

        filas.append(fila)

    # Append a filas para caso sin horas
    for match in matches_sin_horas:
        if match[0] not in nombres_limpios and match[0] not in nombres_sin_por_hora:
            fila = []
            fila.append(match[0])
            fila.append(1)
            fila.append(float(completar_float(match[1])))
            fila.append(float(completar_float(match[2])))

            filas.append(fila)

    # Append al caso shifteado (horas y costo por hora invertidos)
    for match in matches_hora_shifted:
        if match[0] not in nombres_limpios and match[0] not in nombres_sin_por_hora and match[0] not in nombres_sin_horas:
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
    profesiones_fuzzy = [
        'Engineer', 'Scheduler', 'Manager', 'Principal', 'Designer', 'Specialist',
        'Administrative', 'Supervisor', 'Associate', 'Drafter', 'Consultant', 'Director',
        'Analyst', 'Consultant', 'Contractor', 'Extra Hours', 'time entered', 'Assistant',
        'compensation', 'microstation', 'support', 'senior', 'scientist', 'monitoring'
        'expert', 'technical'
    ]

    profesiones_exactas = [
        'phd', '-nda', '- nda', 'cadd', 'sme', 'wfh', 'gis'
    ]

    profesiones_exactas_regex = '|'.join(profesiones_exactas)

    contiene_profesion_fuzzy = df['items'].apply(lambda text: fuzzy_contains(text, profesiones_fuzzy))
    contiene_profesion_exacta = df['items'].str.contains(profesiones_exactas_regex, case=False, na=False)
    contiene_profesion = contiene_profesion_exacta | contiene_profesion_fuzzy

    # Palabras que nunca aparecen en profesiones
    anti_profs = [
        'Client', 'Expense', 'Meal', 'Equipment', 'Admin Fees', ' note'
    ]

    anti_profs_regex = '|'.join([r'\b' + re.escape(anti_prof) + r'\b' for anti_prof in anti_profs])
    no_tiene_antiprof = ~df['items'].str.contains(anti_profs_regex, case=False, na=False)

    # Evalua si tiene un apellido comun
    contiene_apellido_comun = df['items'].str.contains(top_850_apellidos, case=False, na=False)

    # Evalua si la cantidad de horas es distinta a 1
    horas_no_default = (df['horas'] != 1.0) & ((df['precio_por_hora'] - df['total']).abs() > 5)
    horas_implicitas = df.apply(lambda row: is_multiple_or_division(row['precio_por_hora'], row['total']), axis=1)

    horas_profesion = horas_no_default | horas_implicitas

    # Selecciona las filas que tienen costos de servicios profesionales
    rows_prof = df[(contiene_apellido_comun | contiene_profesion | horas_profesion) & no_tiene_antiprof]
    rows_prof = rows_prof.apply(convert_to_same_positivity, axis=1)

    # Calcula finalmente la suma de costo de profesionales
    costo_prof = sum(rows_prof['total'])

    return costo_prof