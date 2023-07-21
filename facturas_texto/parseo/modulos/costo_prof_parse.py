import re
import pandas as pd

# Lectura top 850 apellidos mas comunes en estados unidos (para detectar costos profesionales)
top_nombres_df = pd.DataFrame(pd.read_excel('top_names.xlsx'))
top_nombres_df.columns = top_nombres_df.iloc[1]
top_nombres_df = top_nombres_df.drop(top_nombres_df.index[0])
top_nombres_df = top_nombres_df.drop(top_nombres_df.index[1])

top_850_apellidos = '|'.join([r'\b' + re.escape(surname) + r'\b' for surname in top_nombres_df['SURNAME'][:850]])

# Parsea el costo profesional de una factura
def costo_prof_parse(factura_string):    
   # Crea un objeto que represente las filas de la factura 
    filas = [['items', 'horas', 'precio_por_hora', 'total']]

    texto_relevante = factura_string[factura_string.index('Total') + 5:]
    texto_relevante = '\n' + texto_relevante

    # Regex para distintos casos de filas
    matches_limpios = re.findall(r"\n((?:0?[ a-zA-Z-].+\n){1,2})([ \d.]+)\n([-]?\$[ \d,.]+)\n([-]?\$[ \d,.]+)", texto_relevante)
    matches_cero = re.findall(r"\n(0[ -]?\n)([ \d.]+)\n([-]?\$[ \d,.]+)\n([-]?\$[ \d,.]+)", texto_relevante)
    
    matches_limpios.extend(matches_cero)
    for match in matches_limpios:             
        fila = []
        fila.append(match[0])
        fila.append(float(match[1].replace(',', '').replace('$', '')))
        fila.append(float(match[2].replace(',', '').replace('$', '')))
        fila.append(float(match[3].replace(',', '').replace('$', '')))

        filas.append(fila)

    df = pd.DataFrame(filas)
    df.columns = df.iloc[0]
    df = df.drop(df.index[0])

    # Obtiene el costo de servicios de profesionales

    # Evalua cuales filas se corresponden a trabajos profesionales o tienen un apellido comun
    profesiones = [
        'Engineer', 'Scheduler', 'Manager', 'Principal', 'Designer', 'Specialist',
        'Administrative', 'Supervisor', 'Associate', 'Drafter', 'Consultant', 'Director',
        'Analyst', 'Consultant', 'Contractor', 'Extra Hours', 'SME', 'time entered',
        'WFH', 'Assistant', 'compensation', 'microstation', 'Consutlant', 'Consutianc',
        'support', 'phd', 'senior', 'scientist', '-nda', '- nda', 'cadd', 'monitoring',
        'expert', 'technical', 'gis'
    ]
    
    profesiones_regex = '|'.join(profesiones)

    contiene_apellido_comun = df['items'].str.contains(top_850_apellidos, case=False, na=False)
    contiene_profesion = df['items'].str.contains(profesiones_regex, case=False, na=False)

    # Comprueba que no tenga un keyword asociado a costo no-profesional
    anti_profs = [
        'Client', 'Expense', 'Meal', 'Equipment', 'Admin Fees', 'Credit note', 'amount overdue'
    ]

    anti_profs_regex = '|'.join([r'\b' + re.escape(anti_prof) + r'\b' for anti_prof in anti_profs])

    no_tiene_antiprof = ~df['items'].str.contains(anti_profs_regex, case=False, na=False)

    # Evalua si tiene horas de servicio profesional (distintas a 1)
    horas_no_default = (df['horas'] != 1.0) & ((df['precio_por_hora'] - df['total']).abs() > 5)

    # Selecciona las filas de costos profesionales y calcula su suma
    rows_prof = df[(contiene_apellido_comun | contiene_profesion | horas_no_default) & no_tiene_antiprof]
    costo_prof = sum(rows_prof['total'])
    
    return costo_prof