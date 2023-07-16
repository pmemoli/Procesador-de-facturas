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

# 11966415.pdf, 2021-01-20_689.pdf, 2023-02-21_4480.pdf

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

        if costo_prof > 100000:
            print(path)

        # Estimacion por mediana total
        if costo_prof == 0 and costo_total == -1:
            estimacion = median_tot

        # Estimacion por modelo
        elif abs(costo_prof) < 15 and costo_total != -1:
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

    estimaciones_perdidas_df = pd.DataFrame()
    paths_perdidas = []
    invoices_perdidas = []
    estimaciones_perdidas = []
    for index, row in df_estimaciones.iterrows():
        invoice_df = str(row['Invoice Number']).upper().replace(' ', '')
        estimacion_df = row['Total Charged']
        path_df = row['Path']

        final_invoice_pos = invoice_final['Invoice Number'] == invoice_df
        if sum(final_invoice_pos) != 0:
            invoice_final.loc[final_invoice_pos, 'Total Charged'] = estimacion_df
            completed += 1

        # No se encontro el invoice, se busca salvarlo
        else:
            paths_perdidas.append(path_df)
            invoices_perdidas.append(invoice_df)
            estimaciones_perdidas.append(estimacion_df)

    estimaciones_perdidas_df['Path'] = paths_perdidas
    estimaciones_perdidas_df['Invoice Number'] = invoices_perdidas
    estimaciones_perdidas_df['Total Charged'] = estimaciones_perdidas

    # Se intenta rescatar todas las invoices que se puedan
    salvados = 0

    failed = []
    for index, row in estimaciones_perdidas_df.iterrows():
        invoice_df = row['Invoice Number'].upper().replace(' ', '')
        estimacion_df = row['Total Charged']
        path_df = row['Path']

        has_nan = invoice_final['Total Charged'].isna()
        contains_invoice = invoice_final['Invoice Number'].str.contains(invoice_df)
        filtered_df = invoice_final[contains_invoice & has_nan]

        if not filtered_df.empty and len(filtered_df.index) == 1:
            invoice = filtered_df['Invoice Number'].loc(0)
            invoice_final.loc[invoice_final['Invoice Number'] == invoice, 'Total Charged'] = estimacion_df
            salvados += 1
            failed.append(False)

        else:
            failed.append(True)

    # Repite lo anterior sin el primer elemento del caracter (confusion letra por numero)
    estimaciones_perdidas_restantes_df = estimaciones_perdidas_df[failed]

    for index, row in estimaciones_perdidas_restantes_df.iterrows():
        invoice_df = row['Invoice Number'].upper().replace(' ', '')[1:]
        estimacion_df = row['Total Charged']
        path_df = row['Path']

        has_nan = invoice_final['Total Charged'].isna()
        contains_invoice = invoice_final['Invoice Number'].str.contains(invoice_df)
        filtered_df = invoice_final[contains_invoice & has_nan]

        if not filtered_df.empty and len(filtered_df.index) == 1:
            invoice = filtered_df['Invoice Number'].loc(0)
            invoice_final.loc[invoice_final['Invoice Number'] == invoice, 'Total Charged'] = estimacion_df
            salvados += 1

    perdidas = len(df_estimaciones) - (completed + salvados)
    completed += salvados

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
print(f'Un {porcentaje_no_asociado} % de invoices ({perdidas} de {cantidad_total}) no se lograron asociar\n')

# Las que no se pudieron rescatar se estiman con la mediana
invoice_final['Total Charged'].fillna(value=median_tot, inplace=True)
invoice_final.to_csv('invoice_final_completado.csv')
