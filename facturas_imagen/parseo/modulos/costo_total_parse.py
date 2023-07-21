import re

# Parsea el float en un string.
def completar_float(str, remove_first=True, allow_neg=True):
    constant = 1

    if remove_first:
        if str[0] == '-':
            str = str[2:]
            constant = -1
        else:
            str = str[1:]
    
    if allow_neg:
        cleaned_s = re.sub("[^0-9.,-]", "", str)
    else:
        cleaned_s = re.sub("[^0-9.,]", "", str)

    parts = re.split(r'[.,]', cleaned_s)

    # Si no hay punto hay muchas chances de que este cortado por lo que es mejor perder el dato
    if len(parts) == 1:
        return 0

    # Evalua si la ultima parte es decimal
    if len(parts[-1]) == 2 or len(parts[-1]) == 1:  
        decimal = parts.pop(-1)
    else:
        decimal = None
    
    # El resto de partes representa miles con maybe excepcion del primero
    whole = "".join(parts)

    if whole == '': # Estaba cortado
        return float(re.sub("[,.]", "", cleaned_s))

    number = float(whole)

    if decimal is not None:
        number += float(decimal) / 100

    return number * constant

# Parsea el costo total de una factura
def costo_total_parse(factura_string):
    total_regex = re.findall(r'Total[: -]*\$[.,\d]+', factura_string, re.IGNORECASE)

    # Se encontro correctamente el total
    if len(total_regex) != 0: 
        costo_total = completar_float(total_regex[0], remove_first=False)

    # No se encontro el total, defaultea a -1
    else:
        costo_total = -1

    return costo_total