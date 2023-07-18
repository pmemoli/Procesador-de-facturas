import re

def completar_float(str, remove_first=True):
    if remove_first:
        str = str[1:]
    
    cleaned_s = re.sub("[^0-9.,-]", "", str)
    parts = re.split(r'[.,]', cleaned_s)

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

    return number

print(completar_float('$4,4.5.00', remove_first=True))