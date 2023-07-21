import re

# Parsea el costo total de una factura
def costo_total_parse(factura_string):
    total_regex = re.findall(r'Total:[ ]*\$[.,\d]+', factura_string, re.IGNORECASE)
    if total_regex == []:
        total_regex = re.findall(r'Total:[ ]*-\$[.,\d]+', factura_string, re.IGNORECASE)

    costo_total = total_regex[0].replace('Total:', '').replace(',', '').replace('$', '').replace(' ', '')

    # Salva algunos resultados inconsistentes
    if (costo_total[2] == '.'):
        costo_total = costo_total.replace('.', '', 1)

    costo_total = float(costo_total)

    return costo_total