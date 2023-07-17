ocr_paths = os.listdir('ocr_crudo')
ocr_paths = filter(lambda x : '.joblib' in x, ocr_paths)

for path in ocr_paths:
   parse_all(path, path)
