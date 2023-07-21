from joblib import load
import pandas as pd
import os
import modulos.filtro as filtro

'''
El programa completa el csv provisto por la empresa con numeros de factura y costos vacios.
Lo hace mediante la funcion llenar_invoice(invoice_df) que asocia todos los numeros de factura
posiblea a partir de un dataframe invoice_df.

Antes de correr la funcion se construye un unico dataframe a partir del parseo de facturas en 
formatos de tipo texto e imagen. Luego se corre un filtro sobre cada fila para evaluar si
el dato fue confiable o no. El filtrado se guarda en modulos/filtro.py.
'''

# Modelo (regresion por cuantil)
model, median_tot, median_neg = load('modelo/modelo.joblib')
invoice_model = pd.read_csv('modelo/modelo_df.csv')

# Invoice final a llenar
invoice_final = pd.read_csv('2023-06-26-invoice_numbers-final.csv')
invoice_final['Path'] = None

# Completa el csv provisto por la empresa a partir de los datos de invoice_df
def llenar_invoice(invoice_df):    
    # Aplica las estimaciones para resultados sospechosos
    costo_prof_est, cantidad_modificada = filtro.filtro(invoice_df)

    # Almacena las predicciones en un dataframe df_estimaciones
    df_estimaciones = pd.DataFrame()
    df_estimaciones['Path'] = invoice_df['path']
    df_estimaciones['Invoice Number'] = invoice_df['invoice']
    df_estimaciones['Total Charged'] = costo_prof_est

    completed = 0

    # Busca en el csv provisto por la empresa los invoices de df_estimaciones. Si encuentra una igualdad reemplaza
    # el valor de costo de servicios profesionales 
    failed_primera_it = []
    for index, row in df_estimaciones.iterrows():
        invoice_est = str(row['Invoice Number']).upper().replace(' ', '').replace('(', '').replace(')', '')
        estimacion_df = row['Total Charged']
        path_df = row['Path']

        final_invoice_pos = invoice_final['Invoice Number'] == invoice_est

        if sum(final_invoice_pos) == 1:
            invoice_final.loc[final_invoice_pos, 'Total Charged'] = estimacion_df
            invoice_final.loc[final_invoice_pos, 'Path'] = path_df
            completed += 1
            failed_primera_it.append(False)

        # No se encontro el invoice, se busca salvarlo
        else:
            failed_primera_it.append(True)

    # print(sum(invoice_final['Total Charged'].isna()))
    estimaciones_perdidas_df = df_estimaciones[failed_primera_it]

    # Se intenta rescatar todas las invoices que se puedan viendo si hay un unico invoice en 
    # el csv que CONTENGA al valor que no se pudo asociar
    failed_segunda_it = []
    for index, row in estimaciones_perdidas_df.iterrows():
        invoice_est = str(row['Invoice Number']).upper().replace(' ', '').replace('(', '').replace(')', '')
        estimacion_df = row['Total Charged']
        path_df = row['Path']

        has_nan = invoice_final['Total Charged'].isna()
        contains_invoice = invoice_final['Invoice Number'].str.contains(invoice_est)
        filtered_df = invoice_final[contains_invoice & has_nan]

        if len(filtered_df.index) == 1:
            invoice = filtered_df['Invoice Number'].iloc[0]
            invoice_final.loc[invoice_final['Invoice Number'] == invoice, 'Total Charged'] = estimacion_df
            invoice_final.loc[invoice_final['Invoice Number'] == invoice, 'Path'] = path_df
            completed += 1
            failed_segunda_it.append(False)

        else:
            failed_segunda_it.append(True)

    # Repite lo anterior sin el primer elemento del caracter (confusion letra por numero)
    estimaciones_perdidas_restantes_df = estimaciones_perdidas_df[failed_segunda_it]

    for index, row in estimaciones_perdidas_restantes_df.iterrows():
        invoice_est = str(row['Invoice Number']).upper().replace(' ', '').replace('(', '').replace(')', '')[1:]
        estimacion_df = row['Total Charged']
        path_df = row['Path']

        has_nan = invoice_final['Total Charged'].isna()
        contains_invoice = invoice_final['Invoice Number'].str.contains(invoice_est)
        filtered_df = invoice_final[contains_invoice & has_nan]

        if len(filtered_df.index) == 1:
            invoice = filtered_df['Invoice Number'].iloc[0]
            invoice_final.loc[invoice_final['Invoice Number'] == invoice, 'Total Charged'] = estimacion_df
            invoice_final.loc[invoice_final['Invoice Number'] == invoice, 'Path'] = path_df
            completed += 1

    perdidas = len(df_estimaciones) - completed

    return [cantidad_modificada, perdidas, len(costo_prof_est)]

cantidad_modificada = 0
perdidas = 0
cantidad_total = 0

# Y si uno todos los dataframes?
paths = os.listdir('dataframes')
paths = list(filter(lambda x : '.csv' in x, paths))

ultimate_df = pd.read_csv(f'modelo/modelo_df.csv')

for i in range(len(paths)):
    path_df = pd.read_csv(f'dataframes/{paths[i]}')
    ultimate_df = pd.concat([ultimate_df, path_df])

print('Completando el dataframe...')
cant_mod_ind, perdidas_ind, cant_total_ind = llenar_invoice(ultimate_df)
cantidad_modificada += cant_mod_ind
perdidas += perdidas_ind
cantidad_total += cant_total_ind

porcentaje_reestimado = 100 * round(cantidad_modificada / cantidad_total, 2)
porcentaje_no_asociado = 100 * round(perdidas / cantidad_total, 2)

print(f'\nUn {porcentaje_reestimado} % de valores ({cantidad_modificada} de {cantidad_total}) fueron sospechosos y se re-estimaron')
print(f'Un {porcentaje_no_asociado} % de invoices de los dataframes ({perdidas} de {cantidad_total}) no se lograron asociar')

# Intenta rellenar los invoices que no se pudieron asociar.
for i in range(3):
    print('Rellenando para evitar perdidos...')
    llenar_invoice(ultimate_df)

# Las que no se pudieron rescatar se estiman con la mediana
cantidad_invoice_final = len(invoice_final['Total Charged'])
perdidas_final = sum(invoice_final['Total Charged'].isna())
porcentaje_perdido = 100 * round(perdidas_final / cantidad_invoice_final, 2)

print(f'Un {porcentaje_perdido} % de invoices finales ({perdidas_final} de {cantidad_invoice_final}) no se lograron asociar\n')

invoice_final['Total Charged'].fillna(value=median_tot, inplace=True)
invoice_final.to_csv('invoice_final_completado.csv', index=False)