from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import PyPDF2
import re

def extract_text_from_pdf(pdf_path):
    """PDF dosyasından metin çıkarma"""
    text = ""
    with open(pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        for page in pdf_reader.pages:
            text += page.extract_text()
    return text


def preprocess_text(text):
    """Metni temizleme ve tarih/imza kısımlarını çıkarma"""
    # Tarih formatlarını kaldırma (örn: 01/01/2024, 1 Ocak 2024 vb.)
    text = re.sub(r'\d{1,2}[/.]\d{1,2}[/.]\d{2,4}', '', text)
    text = re.sub(r'\d{1,2}\s+(?:Ocak|Şubat|Mart|Nisan|Mayıs|Haziran|Temmuz|Ağustos|Eylül|Ekim|Kasım|Aralık)\s+\d{4}', '', text)
    
    # İmza bloğunu kaldırma (tipik imza ifadelerini içeren bölümler)
    text = re.sub(r'(?i)(imza|imzalar|adı soyadı|unvan|kaşe).*?\n', '', text)
    
    # Gereksiz boşlukları temizleme
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

print("Temizlenmiş metin:",preprocess_text(extract_text_from_pdf("vs3 - Kopya.pdf")))


def calculate_document_similarity(pdf_path1, pdf_path2, similarity_threshold=0.85):
    """İki PDF dosyası arasındaki benzerliği hesaplama"""
    # Model yüklemesi
    model = SentenceTransformer('dbmdz/bert-base-turkish-cased')
    
    # PDF'lerden metin çıkarma
    text1 = extract_text_from_pdf(pdf_path1)
    text2 = extract_text_from_pdf(pdf_path2)
    
    # Metinleri temizleme
    text1 = preprocess_text(text1)
    text2 = preprocess_text(text2)
    
    # Metinleri paragraf veya bölümlere ayırma
    sections1 = [s.strip() for s in text1.split('\n') if s.strip()]
    sections2 = [s.strip() for s in text2.split('\n') if s.strip()]
    
    # Vektörleştirme
    embeddings1 = model.encode(sections1, convert_to_tensor=True)
    embeddings2 = model.encode(sections2, convert_to_tensor=True)

    print("embeddings1:",embeddings1)
    print("embeddings2:",embeddings2)
    # Benzerlik matrisi hesaplama
    similarity_matrix = cosine_similarity(embeddings1.cpu().numpy(), embeddings2.cpu().numpy())
    
    # Ortalama benzerlik skoru
    average_similarity = np.mean(similarity_matrix)
    
    # En benzer bölümleri bulma
    most_similar_pair = np.unravel_index(np.argmax(similarity_matrix, axis=None), similarity_matrix.shape)
    max_similarity = similarity_matrix[most_similar_pair]
    
    return {
        'average_similarity': average_similarity,
        'max_similarity': max_similarity,
        'is_similar_document': average_similarity >= similarity_threshold,
        'most_similar_sections': {
            'section1': sections1[most_similar_pair[0]],
            'section2': sections2[most_similar_pair[1]],
            'similarity': max_similarity
        }
    }

def check_document_uniqueness(new_pdf_path, existing_pdf_paths, similarity_threshold=0.85):
    """Yeni bir dökümanın mevcut dökümanlarla benzerliğini kontrol etme"""
    results = []
    for existing_pdf in existing_pdf_paths:
        similarity_result = calculate_document_similarity(new_pdf_path, existing_pdf, similarity_threshold)
        results.append({
            'existing_document': existing_pdf,
            'similarity_score': similarity_result['average_similarity'],
            'is_similar': similarity_result['is_similar_document'],
            'most_similar_section': similarity_result['most_similar_sections']
        })
    return results

# Kullanım örneği
if __name__ == "__main__":
    # Yeni gelen döküman
    new_document = "vs3 - Kopya.pdf"
    
    # Mevcut dökümanlar
    existing_documents = [
        "vs3.pdf",
        "vs2.pdf",
        # ... diğer dökümanlar
    ]
    
    # Benzerlik kontrolü
    results = check_document_uniqueness(new_document, existing_documents)
    
    # Sonuçları yazdırma
    for result in results:
        print(f"\nDöküman karşılaştırması: {result['existing_document']}")
        print(f"Benzerlik oranı: {result['similarity_score']*100:.2f}%")
        print(f"Benzer döküman mı?: {'Evet' if result['is_similar'] else 'Hayır'}")
        print("\nEn benzer bölüm:")
        print(f"Bölüm 1: {result['most_similar_section']['section1'][:100]}...")
        print(f"Bölüm 2: {result['most_similar_section']['section2'][:100]}...")
        print(f"Bölüm benzerlik oranı: {result['most_similar_section']['similarity']*100:.2f}%")
