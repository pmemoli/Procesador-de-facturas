from joblib import load
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.linear_model import LinearRegression, QuantileRegressor
import numpy as np
import pandas as pd
import numpy as np

# Lee los resultados de facturas_imagen
invoice_model = pd.read_csv('modelo/modelo_df.csv')

# Implementa el test de hipotesis sobre la proporcion de costo profesional sobre el total
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

# Estima la cdf (cumulative distribution function) con la que se obtiene el p-valor del test.
def cdf(t):
    indice_minimo = (np.abs(rango - t)).argmin() 
    return prob_corresp[indice_minimo]

# Carga los resultados del analisis estadistico en facturas_texto
model, median_tot, median_neg = load('modelo/modelo.joblib')

# Evalua para cada fila de invoice_df cuales datos de costo_profesional amerita re-estimar o no.
# Retorna las estimaciones o el valor original como corresponda.
def filtro(invoice_df):
    costo_prof_est = []
    cantidad_modificada = 0
    for index, row in invoice_df.iterrows():
        costo_prof, costo_total = row['costo_prof'], row['costo_total']
        prediccion_modelo = model.predict(np.array([costo_total]).reshape(-1, 1))[0]

        if costo_total == 0:
            costo_total = -1

        p_valor = cdf(costo_prof / costo_total)

        # Estimacion "default", se queda con lo de ocr
        estimacion = costo_prof

        # Estimacion por mediana total
        if abs(costo_prof) < 30 and abs(costo_total) < 40:
            estimacion = median_tot

        # Estimacion por modelo
        elif abs(costo_prof) < 30 and costo_total != -1:
            if costo_total > 0:
                estimacion = prediccion_modelo
            else:
                estimacion = median_neg

        # Test de hipotesis
        elif (costo_total > 0 and costo_prof > 0) and p_valor < 0.0001:
            estimacion = prediccion_modelo

        costo_prof_est.append(estimacion)

        if estimacion != costo_prof:
            cantidad_modificada += 1

    return costo_prof_est, cantidad_modificada