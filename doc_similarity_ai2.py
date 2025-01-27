import re
import os
import PyPDF2
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

class SentenceComparisonBot:
    def __init__(self, token):
        """Bot Başlatıcı"""
        self.updater = Updater(token)
        self.dp = self.updater.dispatcher
        
        # Komut ve Mesaj İşleyicileri
        self.dp.add_handler(CommandHandler("merhaba", self.start))
        self.dp.add_handler(MessageHandler(Filters.document.mime_type("application/pdf"), self.compare_pdfs))
        
        # PDF'lerin saklanacağı klasör
        self.pdf_folder = "uploaded_pdfs"
        os.makedirs(self.pdf_folder, exist_ok=True)

    def start(self, update: Update, context: CallbackContext):
        """Başlangıç Mesajı"""
        update.message.reply_text(
            "Merhaba! 📄 Ben PDF Sözleşme Karşılaştırma Botuyum.\n"
            "Bana iki farklı PDF göndererek bunları karşılaştırmamı sağlayabilirsiniz."
        )

    def extract_text_from_pdf(self, pdf_path):
        """PDF'den Metin Çıkarma"""
        text = ""
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text()
        return text

    def preprocess_contract(self, text):
        """Sözleşme Metnini Temizleme ve Normalize Etme"""
        # Tarih formatlarını kaldır
        text = re.sub(r'\d{1,2}[/.]\d{1,2}[/.]\d{2,4}', '', text)
        text = re.sub(r'\d{1,2}\s+(?:Ocak|Şubat|Mart|Nisan|Mayıs|Haziran|Temmuz|Ağustos|Eylül|Ekim|Kasım|Aralık)\s+\d{4}', '', text)

        # İmza ve benzeri alanları temizle
        text = re.sub(r'(?i)(imza|kaşe|adı soyadı|unvan).*?:?.*', '', text)

        # Fazla boşlukları temizle ve metni normalize et
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def split_into_sentences(self, text):
        """Metni Cümlelere Bölme"""
        sentences = re.split(r'(?<=[.!?]) +', text)
        return sentences

    def compare_contracts_by_sentences(self, pdf1_path, pdf2_path):
        """İki PDF Sözleşmesini Cümle Bazında Karşılaştır"""
        # PDF'lerden metin çıkarma
        contract1 = self.extract_text_from_pdf(pdf1_path)
        contract2 = self.extract_text_from_pdf(pdf2_path)

        # Metinleri temizleme ve normalize etme
        processed1 = self.preprocess_contract(contract1)
        processed2 = self.preprocess_contract(contract2)

        # Metinleri cümlelere bölme
        sentences1 = set(self.split_into_sentences(processed1))
        sentences2 = set(self.split_into_sentences(processed2))

        # Farklı cümleleri bulma
        unique_to_contract1 = sentences1 - sentences2
        unique_to_contract2 = sentences2 - sentences1

        return {
            'unique_to_contract1': unique_to_contract1,
            'unique_to_contract2': unique_to_contract2,
            'are_identical': not (unique_to_contract1 or unique_to_contract2)
        }

    def compare_pdfs(self, update: Update, context: CallbackContext):
        """Yeni PDF'i mevcut tüm PDF'lerle karşılaştır"""
        try:
            user = update.message.from_user
            
            # Yeni PDF'i geçici olarak kaydet
            file = context.bot.get_file(update.message.document.file_id)
            original_name = update.message.document.file_name
            temp_name = f"temp_{original_name}"
            temp_path = os.path.join(self.pdf_folder, temp_name)
            file.download(temp_path)
            
            update.message.reply_text("📄 PDF alındı, mevcut sözleşmelerle karşılaştırılıyor...")

            # Klasördeki tüm PDF'leri al (geçici dosya hariç)
            existing_pdfs = [
                os.path.join(self.pdf_folder, f)
                for f in os.listdir(self.pdf_folder)
                if f.endswith('.pdf') and f != temp_name
            ]

            if not existing_pdfs:
                # İlk PDF'i kalıcı olarak kaydet
                permanent_path = os.path.join(self.pdf_folder, original_name)
                os.rename(temp_path, permanent_path)
                update.message.reply_text("📝 Bu ilk sözleşme olarak kaydedildi.")
                return

            # Tüm PDF'lerle karşılaştır
            found_match = False
            for existing_pdf in existing_pdfs:
                result = self.compare_contracts_by_sentences(existing_pdf, temp_path)
                
                # Eğer benzerlik oranı %90'dan fazlaysa aynı kabul et
                if result['are_identical'] or len(result['unique_to_contract1']) + len(result['unique_to_contract2']) < 5:
                    update.message.reply_text(
                        f"✅ Bu sözleşme '{os.path.basename(existing_pdf)}' ile aynı!")
                    found_match = True
                    os.remove(temp_path)  # Geçici dosyayı sil
                    break

            if not found_match:
                # Yeni sözleşmeyi kalıcı olarak kaydet
                permanent_path = os.path.join(self.pdf_folder, original_name)
                os.rename(temp_path, permanent_path)
                update.message.reply_text(
                    "❌ Bu yeni bir sözleşme, mevcut sözleşmelerden farklı.\n"
                    "📥 Yeni sözleşme kaydedildi."
                )

        except Exception as e:
            update.message.reply_text(f"❌ Hata oluştu: {str(e)}")
            # Hata durumunda geçici dosyayı temizle
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def run(self):
        """Botu Çalıştır"""
        self.updater.start_polling()
        print("Bot çalışıyor...")
        self.updater.idle()

if __name__ == "__main__":
    BOT_TOKEN = "YOUR_TOKEN"  # BotFather'dan aldığınız token
    bot = SentenceComparisonBot(BOT_TOKEN)
    bot.run()
