import pandas as pd
import numpy as np

# Lee los resultados de facturas_imagen
invoice_model = pd.read_csv('../modelo/modelo_df.csv')

# Estima la distribuciob del cociente entre costo profesional sobre costo total
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