import pandas as pd
import os

print(os.getcwd())
# Da distinto en MIL!!

inv_anteultimo = pd.read_csv('./comparacion_resultados/invoice_final_completado_anteultimo.csv')
inv_ultimo = pd.read_csv('./comparacion_resultados/invoice_final_completado_ultimo.csv')

diferentes_anteultimo = inv_anteultimo[(inv_ultimo['Total Charged'] - inv_anteultimo['Total Charged']).abs() > 3000]
diferentes_ultimo = inv_ultimo[(inv_ultimo['Total Charged'] - inv_anteultimo['Total Charged']).abs() > 3000]

print(diferentes_anteultimo) 
print(diferentes_ultimo)