import re
from collections import Counter

# Parsea el invoice de una factura
def invoice_parse(factura_string, path):
    # Expresiones ideales
    invoice_keys = ['inv', 'locator', 'num', 'invoice']

    pattern_comp_1 = '(' + '|'.join(re.escape(key) for key in invoice_keys) + ')[: .#]*([a-zA-Z]{0,1}[\d]+?)\n'
    pattern_comp_2 = '(' + '|'.join(re.escape(key) for key in invoice_keys) + ')[: .#]*\n([a-zA-Z]{0,1}[\d]+?)\n'

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
        
    # Expresiones mas irregulares
    simple_pattern = '\n([:#])([a-zA-Z]*\d{8,9})\n'
    last_resort_1 = '\n([a-zA-Z]*\d{8,9})\n'
    last_resort_2 = '\n(.*?)([a-zA-Z]*\d{7,9})\n'

    simple_regex = re.findall(simple_pattern, factura_string, re.IGNORECASE)
    last_resort_regex_1 = re.findall(last_resort_1, factura_string, re.IGNORECASE)
    last_resort_regex_2 = re.findall(last_resort_2, factura_string, re.IGNORECASE)

    if fallo:
        simple_regex = re.findall(simple_pattern, factura_string, re.IGNORECASE)
        if simple_regex != []:
            unparsed_inv = simple_regex[0]

        elif last_resort_regex_1 != []:
            unparsed_inv = last_resort_regex_1[0]
        
        else:
            if last_resort_regex_2 != []:
                unparsed_inv = last_resort_regex_2[0]
            else:
                unparsed_inv = ''

    # Guarda el resultado a invoice
    if len(unparsed_inv) == 2:
        if 'amount overdue' in unparsed_inv[0].lower():
            print(unparsed_inv)

        invoice = unparsed_inv[1].replace(' ', '').replace(':', '')
    else:
        invoice = unparsed_inv

    # Filtro para salvar falsos-positivos. Si no fue confiable, toma el nombre del archivo.
    def common_chars(s1, s2):
        return sum((Counter(s1) & Counter(s2)).values())

    nombre_path = path.replace('.pdf', '')
    casi_igual_al_path = len(nombre_path) == len(invoice) and len(invoice) - common_chars(nombre_path, invoice) <= 2
    errado_seguro = len(invoice) < 5 or len(invoice) > 10
    
    if casi_igual_al_path or errado_seguro:
        invoice = nombre_path

    return invoice