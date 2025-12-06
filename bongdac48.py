from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time, random
import json # ADDED
import logging # ADDED

# Thiết lập logging cơ bản để hiển thị lỗi rõ ràng hơn
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s') # ADDED

delay = random.uniform(1.5, 3.0)

url = "https://www.24h.com.vn/bong-da-c48.html"

# HÀM NÀY ĐÃ ĐƯỢC SỬA ĐỂ TRẢ VỀ URL THAY VÌ CHỈ IN RA
def get_all_media(driver):
    """Tìm kiếm và trích xuất URL ảnh và video trong nội dung bài viết."""
    media_urls_picture = set()
    media_urls_video = set()
    
    # 1. ẢNH TRONG BÀI
    img_blocks = driver.find_elements(By.CSS_SELECTOR,
        ("article.cate-24h-foot-arti-deta-info img.news-image" )
    )
    for img in img_blocks:
        src = (
            img.get_attribute("data-original") or 
            img.get_attribute("data-src") or 
            img.get_attribute("src")
        )
        if src and (src.endswith(".jpg") or src.startswith("http")):
            media_urls_picture.add(src)
            
    # 2. VIDEO TRONG BÀI
    video_blocks = driver.find_elements(By.CSS_SELECTOR, "video")
    for video in video_blocks:
        vsrc = video.get_attribute("src") or video.get_attribute("data-src")
        if vsrc:
            media_urls_video.add(vsrc)
            
    # TRẢ VỀ DỮ LIỆU ĐỂ LƯU VÀO JSON
    return list(media_urls_picture), list(media_urls_video)

# HÀM MỚI: XUẤT DỮ LIỆU RA FILE JSON
def export_to_json(data, filename="football_news.json"): # ADDED
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        logging.info(f"Dữ liệu đã được lưu thành công vào file: {filename}")
    except Exception as e:
        logging.error(f"LỖI khi ghi file JSON: {e}")

# Danh sách chứa toàn bộ kết quả thu thập
all_scraped_data = [] # ADDED: Khởi tạo danh sách kết quả

try:
    chrome_options = Options()
    chrome_options.page_load_strategy = "eager"

    driver = webdriver.Chrome(options=chrome_options)
    time.sleep(delay)
    driver.get(url)

    # Lấy danh sách bài
    WebDriverWait(driver, 20).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "h3"))
    )

    list_data = []
    links = driver.find_elements(By.CSS_SELECTOR, "h3 a")

    for a in links:
        list_data.append({
            "title": a.text.strip(),
            "url": a.get_attribute("href")
        })

    # 1. GIỚI HẠN CHỈ LẤY 10 BÀI MỚI NHẤT
    list_data = list_data[:10] # ADDED: Limit to top 10 articles

    print(f"Đã tìm {len(list_data)} bài.\n")

    main_url = url

    for i, data in enumerate(list_data, 1):
        print(f"--- ({i}/{len(list_data)}) {data['title']} , {data['url']}")

        try:
            time.sleep(delay)
            driver.get(data["url"])

            # Chờ nội dung xuất hiện
            WebDriverWait(driver, 20).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "article"))
            )

            # Lấy Media (Ảnh và Video)
            pictures_url, videos_url = get_all_media(driver) # MODIFIED CALL
            
            # Lấy Meta Description (Sapo)
            try:
                meta_element = driver.find_element(By.CSS_SELECTOR, "main.main-24h header header a")
                meta_description = meta_element.get_attribute("title")
            except:
                meta_description = "N/A"

            # Lấy Full Content Text
            try:
                # ------------------- MODIFICATION START -------------------
                # Tìm tất cả các thẻ <p> trong khối nội dung chính (#page_detail)
                content_paragraphs = driver.find_elements(By.CSS_SELECTOR, "article.cate-24h-foot-arti-deta-info p")
                
                # Nối tất cả các đoạn văn bản lại với nhau
                full_content_text = "\n\n".join([p.text.strip() for p in content_paragraphs if p.text.strip()])
                
                if not full_content_text:
                    full_content_text = "N/A (Could not find <p> tags in #page_detail)"

                # ------------------- MODIFICATION END -------------------
            except:
                full_content_text = "N/A (Error during content extraction)"

            # Lấy Important Text
            strong_blocks = driver.find_elements(By.CSS_SELECTOR, "article strong")
            important_text = []
            for s in strong_blocks:
                text = s.text.strip()
                if len(text) > 30:
                    important_text.append(text)

            # 2. LƯU TẤT CẢ THÔNG TIN VÀO DICTIONARY
            article_data = { # ADDED: Data structure for JSON
                "id": i,
                "title": data['title'],
                "url": data['url'],
                "meta_description": meta_description,
                "important_text": important_text,
                "full_content_text": full_content_text,
                "pictures_url": pictures_url,
                "videos_url": videos_url,
            }
            all_scraped_data.append(article_data) # ADDED: Lưu vào danh sách

            print(f"  -> [OK] Đã thu thập xong chi tiết.")

            driver.get(main_url)

        except Exception as e:
            error_message = f"Lỗi cào chi tiết: {e}"
            logging.error(f"!!! Lỗi xử lý {data['url']}: {error_message}")
            all_scraped_data.append({ # ADDED: Ghi lại lỗi
                "id": i,
                "url": data['url'],
                "title": data['title'],
                "error": error_message
            })
            driver.get(main_url)

    driver.quit()
    
    # 3. XUẤT JSON (Chạy sau khi vòng lặp kết thúc)
    export_to_json(all_scraped_data) # ADDED: Xuất file JSON

except Exception as e:
    print("LỖI:", e)