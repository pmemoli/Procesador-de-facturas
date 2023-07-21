import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import QuantileRegressor
from sklearn.model_selection import cross_val_score
from sklearn.metrics import mean_absolute_error, mean_squared_error
from joblib import dump

factura_parsed = pd.read_csv('modelo_df.csv')

# Los valores positivos y negativos de total reciben distintos tratamientos. El modelo lineal solo es para costo total mayor a 0.
df_pos = factura_parsed[factura_parsed['costo_total'] > 0]
df_neg = factura_parsed[factura_parsed['costo_total'] <= 0]

# En terminos estadisticos la "respuesta" es el costo profesional y la "covariable" es el costo total
cov = np.array(df_pos['costo_total']).reshape(-1, 1)
res = np.array(df_pos['costo_prof']).reshape(-1, 1)

# Corre la regresion por cuantil de sklearn
def quantile_regression():
    model = QuantileRegressor(quantile=0.5, solver='highs').fit(cov, res.ravel())

    ecm = mean_squared_error(res, model.predict(cov))
    eam = mean_absolute_error(res, model.predict(cov))

    return ecm, eam, model 

# Modelo para valores de costo total positivo (regresion por cuantil)
ecm_quant, eam_quant, model_quant = quantile_regression()

# Modelo para valores con costo total negativo (estima por la mediana)
median_neg = np.median(np.sort(df_neg['costo_prof']))

# Modelo para valores sin costo total (estima por la mediana)
median_tot = np.median(np.sort(factura_parsed['costo_prof']))

# Plotea para mas claridad
x = np.linspace(min(cov), max(cov))
plt.plot(x, model_quant.predict(x), label=f'Regresion por Cuantil, EAM: {round(eam_quant, 2)}', color='orange')
plt.scatter(cov, res, color='blue', s=5)

plt.xlabel('Costo Total')
plt.ylabel('Costo Profesionales')
plt.legend()
plt.grid()
plt.show()

# Guarda los objetos como un archivo .joblib
dump([model_quant, median_tot, median_neg], 'modelo.joblib')
