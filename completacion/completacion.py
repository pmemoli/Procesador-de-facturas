from joblib import load
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.linear_model import LinearRegression, QuantileRegressor
import numpy as np
import os

# Modelo (regresion por cuantil) y test de hipotesis (sobre relacion prof/total)
model, median_tot, median_neg = load('modelo/modelo.joblib')

invoice_model = pd.read_csv('modelo/modelo_df.csv')

proporcion = pd.DataFrame()
proporcion['proporcion'] = invoice_model['costo_prof'] / invoice_model['costo_total']
proporcion['path'] = invoice_model['path']

casos_sospechosos = proporcion[proporcion['proporcion'].abs() < 0.02]

proporcion_no_neg = proporcion[proporcion['proporcion'] > 0]

rango = np.linspace(0, 10, 3000)
prob_corresp = []
n = len(proporcion_no_neg['proporcion'])
for x in rango:
    empirica = (proporcion_no_neg['proporcion'] < x).sum() / n
    prob_corresp.append(empirica)

def cdf(t):
    indice_minimo = (np.abs(rango - t)).argmin() 
    return prob_corresp[indice_minimo]

# Invoice final a llenar
invoice_final = pd.read_csv('2023-06-26-invoice_numbers-final.csv')
invoice_final['Path'] = None

def llenar_invoice(path_df):    
    invoice_df = pd.read_csv(path_df)

    # Aplica las estimaciones para resultados sospechosos
    costo_prof_est = []
    cantidad_modificada = 0
    for index, row in invoice_df.iterrows():
        path = row['path']
        costo_prof, costo_total = row['costo_prof'], row['costo_total']
        prediccion_modelo = model.predict(np.array([costo_total]).reshape(-1, 1))[0]

        p_valor = cdf(costo_prof / costo_total)

        # Estimacion "default", se queda con lo de ocr
        estimacion = costo_prof

        # if costo_prof != 0 and costo_prof < 130:
        #     print(path, costo_prof, costo_total, p_valor)

        # Estimacion por mediana total
        if costo_prof == 0 and abs(costo_total) < 40:
            estimacion = median_tot

        # Estimacion por modelo
        elif abs(costo_prof) < 30 and costo_total != -1:
            if costo_total > 0:
                estimacion = prediccion_modelo
            else:
                estimacion = median_neg

        # Test de hipotesis
        elif costo_total > 0 and p_valor < 0.0001:
            estimacion = prediccion_modelo

        costo_prof_est.append(estimacion)

        if estimacion != costo_prof:
            cantidad_modificada += 1

    df_estimaciones = pd.DataFrame()
    df_estimaciones['Path'] = invoice_df['path']
    df_estimaciones['Invoice Number'] = invoice_df['invoice']
    df_estimaciones['Total Charged'] = costo_prof_est

    # Agregado al dataframe invoice final
    completed = 0

    failed_primera_it = []
    for index, row in df_estimaciones.iterrows():
        invoice_df = str(row['Invoice Number']).upper().replace(' ', '').replace('(', '').replace(')', '')
        estimacion_df = row['Total Charged']
        path_df = row['Path']

        final_invoice_pos = invoice_final['Invoice Number'] == invoice_df
        if sum(final_invoice_pos) != 0:
            invoice_final.loc[final_invoice_pos, 'Total Charged'] = estimacion_df
            invoice_final.loc[final_invoice_pos, 'Path'] = path_df
            completed += 1
            failed_primera_it.append(False)

        # No se encontro el invoice, se busca salvarlo
        else:
            failed_primera_it.append(True)

    estimaciones_perdidas_df = df_estimaciones[failed_primera_it]

    # Se intenta rescatar todas las invoices que se puedan viendo contenciones
    failed_segunda_it = []
    for index, row in estimaciones_perdidas_df.iterrows():
        invoice_df = str(row['Invoice Number']).upper().replace(' ', '').replace('(', '').replace(')', '')
        estimacion_df = row['Total Charged']
        path_df = row['Path']

        has_nan = invoice_final['Total Charged'].isna()
        contains_invoice = invoice_final['Invoice Number'].str.contains(invoice_df)
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
        invoice_df = str(row['Invoice Number']).upper().replace(' ', '').replace('(', '').replace(')', '')[1:]
        estimacion_df = row['Total Charged']
        path_df = row['Path']

        has_nan = invoice_final['Total Charged'].isna()
        contains_invoice = invoice_final['Invoice Number'].str.contains(invoice_df)
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

cant_mod_ind, perdidas_ind, cant_total_ind = llenar_invoice('modelo/modelo_df.csv')
cantidad_modificada += cant_mod_ind
perdidas += perdidas_ind
cantidad_total += cant_total_ind

paths = os.listdir('dataframes')
for path in paths:
    print(f'Completando los datos de {path}')
    cant_mod_ind, perdidas_ind, cant_total_ind = llenar_invoice(f'dataframes/{path}')

    cantidad_modificada += cant_mod_ind
    perdidas += perdidas_ind
    cantidad_total += cant_total_ind

porcentaje_reestimado = 100 * round(cantidad_modificada / cantidad_total, 2)
porcentaje_no_asociado = 100 * round(perdidas / cantidad_total, 2)

print(f'\nUn {porcentaje_reestimado} % de valores ({cantidad_modificada} de {cantidad_total}) fueron sospechosos y se re-estimaron')
print(f'Un {porcentaje_no_asociado} % de invoices de los dataframes ({perdidas} de {cantidad_total}) no se lograron asociar')

for path in paths:
    print(f'Completando los datos de {path}')
    cant_mod_ind, perdidas_ind, cant_total_ind = llenar_invoice(f'dataframes/{path}')

for path in paths:
    print(f'Completando los datos de {path}')
    cant_mod_ind, perdidas_ind, cant_total_ind = llenar_invoice(f'dataframes/{path}')

# Las que no se pudieron rescatar se estiman con la mediana
cantidad_invoice_final = len(invoice_final['Total Charged'])
perdidas_final = sum(invoice_final['Total Charged'].isna())
porcentaje_perdido = 100 * round(perdidas_final / cantidad_invoice_final, 2)

print(f'Un {porcentaje_perdido} % de invoices finales ({perdidas_final} de {cantidad_invoice_final}) no se lograron asociar\n')

invoice_final['Total Charged'].fillna(value=median_tot, inplace=True)
invoice_final.to_csv('invoice_final_completado.csv', index=False)

# 248266849.pdf, A99436936.pdf, Invoice (3221).pdf