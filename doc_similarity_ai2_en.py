import re
import PyPDF2

def extract_text_from_pdf(file_path):
    """PDF dosyasından metin çıkarma."""
    text = ""
    with open(file_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        for page in pdf_reader.pages:
            text += page.extract_text()
    return text

def preprocess_contract(text):
    """Metni temizler ve normalize eder (İngilizce için)."""
    # Tarihleri kaldır (örneğin: "January 1, 2024", "01/01/2024")
    text = re.sub(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', '', text)  # Tarih formatı: 01/01/2024
    text = re.sub(r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\b \d{1,2}, \d{4}', '', text, flags=re.IGNORECASE)

    # İmza ve ilgili alanları temizle
    text = re.sub(r'(?i)(signature|signatures|name|title).*?:?.*', '', text)
    
    # Para birimlerini normalize et
    text = re.sub(r'[\$£€]\d+([.,]\d+)?', '$value', text)
    
    # Fazla boşlukları temizle ve metni normalize et
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def split_into_sentences(text):
    """Metni cümlelere böler."""
    sentences = re.split(r'(?<=[.!?]) +', text)
    return sentences

def compare_contracts_by_sentences(pdf_path1, pdf_path2):
    """İki PDF sözleşmesini cümle bazında karşılaştırır."""
    # PDF'lerden metin çıkarma
    contract1 = extract_text_from_pdf(pdf_path1)
    contract2 = extract_text_from_pdf(pdf_path2)
    
    # Sözleşme metinlerini ön işlemden geçir
    processed1 = preprocess_contract(contract1)
    processed2 = preprocess_contract(contract2)
    
    # Metinleri cümlelere ayırma
    sentences1 = set(split_into_sentences(processed1))
    sentences2 = set(split_into_sentences(processed2))
    
    # Farklı cümleleri bulma
    unique_to_contract1 = sentences1 - sentences2
    unique_to_contract2 = sentences2 - sentences1
    
    return {
        'unique_to_contract1': unique_to_contract1,
        'unique_to_contract2': unique_to_contract2,
        'are_identical': not (unique_to_contract1 or unique_to_contract2)
    }

# Örnek Kullanım
if __name__ == "__main__":
    # İngilizce PDF dosyalarının yolları
    pdf1_path = "contract1.pdf"
    pdf2_path = "contract2.pdf"

    # Karşılaştırma
    result = compare_contracts_by_sentences(pdf1_path, pdf2_path)

    # Sonuçları yazdırma
    if result['are_identical']:
        print("Contracts are identical.")
    else:
        print("Contracts differ.")
        print("\nUnique to Contract 1:")
        for sentence in result['unique_to_contract1']:
            print("-", sentence)
        
        print("\nUnique to Contract 2:")
        for sentence in result['unique_to_contract2']:
            print("-", sentence)


##########tr##########
import re
import PyPDF2

def extract_text_from_pdf(file_path):
    """PDF dosyasından metin çıkarma."""
    text = ""
    with open(file_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        for page in pdf_reader.pages:
            text += page.extract_text()
    return text

def preprocess_contract(text):
    """Sözleşme metnini temizler ve normalize eder."""
    # Tarih formatlarını kaldır (örneğin: 01/01/2024 veya 1 Ocak 2024)
    text = re.sub(r'\d{1,2}[/.]\d{1,2}[/.]\d{2,4}', '', text)
    text = re.sub(r'\d{1,2}\s+(?:Ocak|Şubat|Mart|Nisan|Mayıs|Haziran|Temmuz|Ağustos|Eylül|Ekim|Kasım|Aralık)\s+\d{4}', '', text)
    
    # İmza, unvan, kaşe ve ilgili alanları temizle
    text = re.sub(r'(?i)(imza|kaşe|adı soyadı|unvan).*?:?.*', '', text)
    
    # "1. Taraflar" başlığını ve ilgili bölümü kaldır
    text = re.sub(r'1\\. Taraflar.*?(2\\.|Sözleşmenin Konusu)', '2. ', text, flags=re.DOTALL)

    # Para birimlerini normalize et (örneğin: "$1000" -> "$değer")
    text = re.sub(r'\$\d+([.,]\d+)?', '$değer', text)
    
    # Fazla boşlukları temizle ve metni normalize et
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def split_into_sentences(text):
    """Metni cümlelere böler."""
    # Nokta, soru işareti ve ünlem ile biten cümlelere göre bölme
    sentences = re.split(r'(?<=[.!?]) +', text)
    return sentences

def compare_contracts_by_sentences(pdf_path1, pdf_path2):
    """İki PDF sözleşmesini cümle bazında karşılaştırır."""
    # PDF'lerden metin çıkarma
    contract1 = extract_text_from_pdf(pdf_path1)
    contract2 = extract_text_from_pdf(pdf_path2)
    
    # Sözleşme metinlerini ön işlemden geçir
    processed1 = preprocess_contract(contract1)
    processed2 = preprocess_contract(contract2)
    
    # Metinleri cümlelere ayırma
    sentences1 = set(split_into_sentences(processed1))
    sentences2 = set(split_into_sentences(processed2))
    
    # Farklı cümleleri bulma
    unique_to_contract1 = sentences1 - sentences2
    unique_to_contract2 = sentences2 - sentences1
    
    return {
        'unique_to_contract1': unique_to_contract1,
        'unique_to_contract2': unique_to_contract2,
        'are_identical': not (unique_to_contract1 or unique_to_contract2)
    }

# Örnek Kullanım
if __name__ == "__main__":
    # Karşılaştırılacak PDF dosyalarının yolları
    pdf1_path = "sozlesme1.pdf"
    pdf2_path = "sozlesme2.pdf"

    # Karşılaştırma
    result = compare_contracts_by_sentences(pdf1_path, pdf2_path)

    # Sonuçları yazdırma
    if result['are_identical']:
        print("Sözleşmeler tamamen aynıdır.")
    else:
        print("Sözleşmeler farklıdır.")
        print("\nSözleşme 1'e özgü cümleler:")
        for sentence in result['unique_to_contract1']:
            print("-", sentence)
        
        print("\nSözleşme 2'ye özgü cümleler:")
        for sentence in result['unique_to_contract2']:
            print("-", sentence)
