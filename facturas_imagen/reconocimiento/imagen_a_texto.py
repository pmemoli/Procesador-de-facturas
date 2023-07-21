import cv2
from PIL import Image
from pdf2image import convert_from_path
import numpy as np
import matplotlib.pyplot as plt
from skimage import io
from skimage.transform import rotate
from skimage.color import rgb2gray
from deskew import determine_skew
from paddleocr import PaddleOCR, draw_ocr
from joblib import dump
import os

'''
El programa procesa todas las imagenes en la carpeta de ./imagenes. Corre un algoritmo
de OCR (optical character recognition) utilizando PaddleOCR y almacena los resultados en chunks
de 100 imagenes procesadas en la carpeta de ./ocr_crudo.
'''

# Inicializa el objeto de PaddleOCR
ocr = PaddleOCR(lang='en', use_angle_cls=False)

# Plotea una imagen en formato array de numpy (para testear)
def plot_img(img):
    cv2.namedWindow('image', cv2.WINDOW_NORMAL)
    cv2.imshow('image', img)
    cv2.resizeWindow('image', 1000, 1000)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

# Convierte un pdf en una lista de imagenes pre-procesadas donde cada imagen es una pagina del pdf. 
def pdf_to_images(pdf_path):
    pil_images = convert_from_path(pdf_path)

    # Se representan las imagenes como arrays de numpy
    np_images = [np.array(pil_image) for pil_image in pil_images]

    # Aplica el pre-procesado. Convierte cada imagen a escala de grises y las endereza
    cv_images = []
    for img in np_images:
        grayscale = rgb2gray(img)
        angle = determine_skew(grayscale)
        rotated_grey = (rotate(grayscale, angle, resize=True) * 255).astype(np.uint8)
        rotated = cv2.cvtColor(rotated_grey, cv2.COLOR_GRAY2RGB)

        cv_images.append(rotated)

    return cv_images

# Aplica PaddleOCR sobre una imagen en formato array de numpy
def apply_paddleocr(img, plot=False):
    result = ocr.ocr(img, cls=False)

    if plot:
        result = result[0]
        boxes = [line[0] for line in result]
        txts = [line[1][0] for line in result]
        scores = [line[1][1] for line in result]
        im_show = draw_ocr(img, boxes, txts, scores, font_path='ocr_crudo/ocr_test_resources/Roboto.ttf')
        im_show = Image.fromarray(im_show)

        im_show.save('ocr_crudo/ocr_test_resources/result.jpg')

    return result

# Itera sobre cada pdf en ./imagenes y guarda el reconocimiento en la carpeta de ocr_crudo (formato joblib)
path_images = os.listdir('imagenes')
path_images = list(filter(lambda x : '.pdf' in x, path_images))

path_ocr = os.listdir('ocr_crudo')
path_ocr = list(filter(lambda x : '.joblib' in x, path_ocr))

# Particiona las imagenes en chunks de 100 para guardarlas luego de que se proceso todo el chunk
n = 100
partitions = [list(range(i, i + n)) for i in range(0, len(path_images), n)]

for partition in partitions:
    rango_string = f'{partition[0]}-{partition[-1]}'

    # Comprueba que no haya un archivo en ocr_crudo que contenga el procesamiento del chunk
    if not any(f'{rango_string}' in s for s in path_ocr):
        # Documentos es una lista con el resultado de cada chunk de archivos.
        ocr_documentos = []
        cantidad_trabajada = partition[0] - 1
        for part_index in partition:
            if part_index < len(path_images):
                img_pags = pdf_to_images('imagenes/' + path_images[part_index])

                ocr_pags = []
                for img in img_pags:
                    ocr_pags.append(apply_paddleocr(img, plot=False)[0])

                ocr_documento = []
                for pag in ocr_pags:
                    for item in pag:
                        ocr_documento.append(item)

                ocr_documentos.append({'path': path_images[part_index], 'text': ocr_documento})

                cantidad_trabajada += 1

                print(f'\nTerminado {cantidad_trabajada} de {len(path_images)}\n')

        dump(ocr_documentos, f'ocr_crudo/ocr_img_{partition[0]}-{partition[-1]}.joblib')

    else:
        print(f'\nRango {rango_string} ya trabajado')
