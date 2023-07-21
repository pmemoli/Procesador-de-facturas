from collections import Counter
import re

# Parsea el invoice de una factura
def invoice_parse(factura_string, path, safe=True):
    factura_string = '\n' + factura_string

    # Todos los invoices tienen por lo menos 6 digitos. Si se usa el modo safe=False reconoce como minimo 5 digitos
    # para asi detectar invoices que fueron "cortados"
    if safe:
        minimum = '6'
    else:
        minimum = '5'

    # Patrones ideales
    invoice_keys = ['inv', 'cator', 'num', 'oice']

    # Hubo cambios aca
    pattern_comp_1 = '(' + '|'.join(re.escape(key) for key in invoice_keys) + ')[: .#]*([a-zA-Z]?\d*[a-zA-Z]?\d+).?\n'
    pattern_comp_2 = '\n([:# ])([a-zA-Z]{0,1}\d{' + minimum + ',9}).{0,1}\n'

    invoice_regex_1 = re.findall(pattern_comp_1, factura_string, re.IGNORECASE)
    invoice_regex_2 = re.findall(pattern_comp_2, factura_string, re.IGNORECASE)

    invoice_regex_1 = list(filter(lambda x : 'issued' not in x[1], invoice_regex_1))
    invoice_regex_2 = list(filter(lambda x : 'issued' not in x[1], invoice_regex_2))

    fallo = False
    if invoice_regex_1 != []:
        unparsed_inv = invoice_regex_1[0]
    
    elif invoice_regex_2 != []:
        unparsed_inv = invoice_regex_2[0]
    
    else:
        fallo = True
        
    # Patrones mas irregulares
    last_resort_1 = '\n(.*)\n([a-zA-Z]{0,1}\d{' + minimum + ',9}).{0,1}\n'
    last_resort_2 = '\n(.*?)([a-zA-Z]{0,1}\d{' + minimum + ',9}).{0,1}\n'

    last_resort_regex_1 = re.findall(last_resort_1, factura_string, re.IGNORECASE)
    last_resort_regex_2 = re.findall(last_resort_2, factura_string, re.IGNORECASE)

    if fallo:
        if last_resort_regex_1 != []:
            unparsed_inv = last_resort_regex_1[0]
        
        else:
            if last_resort_regex_2 != []:
                unparsed_inv = last_resort_regex_2[0]
            else:
                unparsed_inv = ''

    # Detecta invoices mal parseados
    pattern = r"(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)"

    if len(unparsed_inv) == 2:
        not_overdue = 'overdue' not in unparsed_inv[0].lower()
        accepted_keywords = 'invoice locator' in unparsed_inv[0].lower() or 'invoice loeator' in unparsed_inv[0].lower() or 'Yenerated Tnvoice' in unparsed_inv[0].lower() 
        proper_width = len(unparsed_inv[0]) < 16 or accepted_keywords
        no_month = re.findall(pattern, unparsed_inv[0], re.IGNORECASE) == []

        if not_overdue and proper_width and no_month:
            invoice = unparsed_inv[1].replace(' ', '').replace(':', '')
        else:
            invoice = ''
    else:
        invoice = unparsed_inv

    # Evaluacion final
    def common_chars(s1, s2):
        return sum((Counter(s1) & Counter(s2)).values())

    nombre_path = path.replace('.pdf', '')
    casi_igual_al_path = len(nombre_path) == len(invoice) and len(invoice) - common_chars(nombre_path, invoice) <= 2
    errado_seguro = len(invoice) < 6 or len(invoice) > 10
    en_path = (re.findall('[a-zA-Z]*\d{7,9}', nombre_path) != []) and len(nombre_path) < 11
    
    # En ningun invoice hay caracteres mas alla del primero, los reemplaza si aparecen
    if invoice != '':
        primer_car = invoice[0]
        resto = invoice[1:]

        resto = re.sub('i', '1', resto, flags=re.I)
        resto = re.sub('f', '1', resto, flags=re.I)
        resto = re.sub('l', '1', resto, flags=re.I)
        resto = re.sub('s', '5', resto, flags=re.I)
        resto = re.sub('o', '0', resto, flags=re.I)
        resto = re.sub('k', '4', resto, flags=re.I)

        invoice = primer_car + resto

    if casi_igual_al_path or en_path:
        invoice = nombre_path

    elif errado_seguro:
        if invoice == '' and safe:
            invoice = invoice_parse(factura_string, path, safe=False)

    return invoice