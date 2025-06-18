import pytesseract
from PIL import Image
import io

def ocr_from_image(file) -> str:
    """
    Przyjmuje plik obrazu (np. JPG, PNG) i zwraca rozpoznany tekst.
    """
    img = Image.open(file)
    text = pytesseract.image_to_string(img, lang='pol')
    return text
