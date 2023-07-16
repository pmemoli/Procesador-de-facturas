import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression, QuantileRegressor
from sklearn.neighbors import KNeighborsRegressor
from sklearn.model_selection import LeaveOneOut
from sklearn.model_selection import cross_val_score
from sklearn.metrics import mean_absolute_error, mean_squared_error
from joblib import dump

factura_parsed = pd.read_csv('modelo_df.csv')
df_pos = factura_parsed[factura_parsed['costo_total'] > 0]
df_neg = factura_parsed[factura_parsed['costo_total'] <= 0]

cov = np.array(df_pos['costo_total']).reshape(-1, 1)
res = np.array(df_pos['costo_prof']).reshape(-1, 1)

def modelo_lineal():
    model = LinearRegression().fit(cov, res)

    ecm = mean_squared_error(res, model.predict(cov))
    eam = mean_absolute_error(res, model.predict(cov))

    return ecm, eam, model 

def quantile_regression():
    model = QuantileRegressor(quantile=0.5, solver='highs').fit(cov, res.ravel())

    ecm = mean_squared_error(res, model.predict(cov))
    eam = mean_absolute_error(res, model.predict(cov))

    return ecm, eam, model 

def knn():
    vecinos = range(1, 15)
    cv_score = []

    for n in vecinos:
        neigh = KNeighborsRegressor(n)

        cv = LeaveOneOut()
        scores = cross_val_score(neigh, cov, res, scoring='neg_mean_absolute_error',
                         cv=cv, n_jobs=-1)
        
        cv_score.append(np.mean(np.absolute(scores)))

    mejor_n = vecinos[np.argmin(cv_score)]
    neigh = KNeighborsRegressor(mejor_n).fit(cov, res)

    ecm = mean_squared_error(res, neigh.predict(cov))
    eam = mean_absolute_error(res, neigh.predict(cov))

    return ecm, eam, neigh

# Modelo para valores de total positivos
#ecm_knn, eam_knn, model_knn = knn()
ecm_lin, eam_lin, model_lin = modelo_lineal()
ecm_quant, eam_quant, model_quant = quantile_regression()

# Modelo para valores de total negativos (estima por la mediana)
median_neg = np.median(np.sort(df_neg['costo_prof']))

# Modelo para valores sin covariables
median_tot = np.median(np.sort(factura_parsed['costo_prof']))

print(median_neg, median_tot)

x = np.linspace(min(cov), max(cov))
#plt.plot(x, model_knn.predict(x), label=f'Knn, EAM: {round(eam_knn, 2)}')
plt.plot(x, model_lin.predict(x), label=f'Regresion Lineal, EAM: {round(eam_lin, 2)}')
plt.plot(x, model_quant.predict(x), label=f'Regresion por Cuantil, EAM: {round(eam_quant, 2)}')
plt.scatter(cov, res, color='blue', s=5)

plt.xlabel('Costo Total')
plt.ylabel('Costo Profesionales')
plt.legend()
plt.grid()
plt.show()

'''
Para valores positivos, la regresion por cuatil minimiza el eam y no overfittea. La considero la regresion
mas adecuada para predecir las imagenes a las que no se les pueda hacer ocr.
Para valores negativos se rompe la correlacion asi que hago predicciones simplemente con la mediana.
'''

dump([model_quant, median_tot, median_neg], 'modelo.joblib')
