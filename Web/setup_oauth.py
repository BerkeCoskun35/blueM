from ytmusicapi import YTMusic
import json

print("YouTube Music API kimlik doğrulama dosyası oluşturuluyor...")
print("Lütfen aşağıdaki adımları takip edin:")
print("1. Chrome tarayıcısını açın ve music.youtube.com adresine gidin")
print("2. F12 tuşuna basarak geliştirici araçlarını açın")
print("3. Network sekmesine tıklayın")
print("4. Sayfayı yenileyin")
print("5. İlk isteği seçin (genellikle 'browse' veya 'main')")
print("6. Headers sekmesinde 'Request Headers' bölümünü bulun")
print("7. Cookie değerini kopyalayın")
print("\nŞimdi cookie değerini yapıştırın ve Enter'a basın:")

headers_raw = input().strip()

if not headers_raw:
    print("Hata: Cookie değeri boş olamaz!")
    exit(1)

if not headers_raw.startswith("cookie:"):
    print("Hata: Cookie değeri 'cookie:' ile başlamalıdır!")
    print("Örnek: cookie: VISITOR_INFO1_LIVE=...; VISITOR_PRIVACY_METADATA=...")
    exit(1)

try:
    # Cookie değerini düzenle
    cookie_value = headers_raw.replace("cookie:", "").strip()
    
    # OAuth dosyasını oluştur
    oauth_data = {
        "cookie": cookie_value,
        "x-goog-authuser": "0",
        "x-origin": "https://music.youtube.com"
    }

    with open("oauth.json", "w", encoding="utf-8") as f:
        json.dump(oauth_data, f, indent=4)

    print("\nKimlik doğrulama dosyası oluşturuldu. Şimdi test ediyorum...")

    # Test bağlantısı
    ytmusic = YTMusic("oauth.json")
    search_results = ytmusic.search("test", filter="songs", limit=1)
    print("Bağlantı başarılı! Sistem hazır.")
except Exception as e:
    print(f"Hata oluştu: {str(e)}")
    print("Lütfen tekrar deneyin.") 