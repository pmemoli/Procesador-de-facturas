import pandas as pd
import numpy as np

df_ocr = pd.read_csv('dataframes/ocr_df.csv')
df_true = pd.read_csv('dataframes/modelo_df.csv')

filas_relev = df_ocr[df_ocr['invoice'].isin(df_true['invoice'])]

diferencias_total = []
diferencias_prof = []

for i in range(len(df_ocr['invoice'])):
    invoice = str(df_ocr['invoice'][i]).lower()
    row_real = df_true.loc[df_true['invoice'].str.lower() == invoice]

    if not row_real.empty:
        diferencia_total = abs(row_real['costo_total'].iloc[0] - df_ocr['costo_total'][i])
        diferencias_total.append(diferencia_total)

        diferencia_prof = abs(row_real['costo_prof'].iloc[0] - df_ocr['costo_prof'][i])
        diferencias_prof.append(diferencia_prof)

        if (diferencia_prof > 1 or diferencia_total > 1):
            print(row_real['costo_prof'].iloc[0], df_ocr['costo_prof'][i], df_ocr['path'][i])

    else:
        print(df_ocr['path'][i])


eam_total = np.linalg.norm(np.array(diferencias_total), ord=1) / len(diferencias_total)
eam_prof = np.linalg.norm(np.array(diferencias_prof), ord=1) / len(diferencias_prof)

print(f'\nEl eam total es: {eam_total} y el prof {eam_prof}')
