from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time, random

delay = random.uniform(1.5, 3.0)

url = "https://vnexpress.net/bat-dong-san"

try:
    chrome_options = Options()
    chrome_options.page_load_strategy = "eager"

    driver = webdriver.Chrome(options=chrome_options)
    driver.set_page_load_timeout(30)
    time.sleep(delay)
    
    driver.get(url)

    WebDriverWait(driver, 20).until(
        EC.presence_of_all_elements_located((By.TAG_NAME, "h3"))
    )

    # Lấy danh sách bài
    list_data = []
    articles = driver.find_elements(By.CSS_SELECTOR, "h3 a")

    for a in articles:
        list_data.append({
            "title": a.text.strip(),
            "url": a.get_attribute("href")
        })

    print(f"Đã tìm thấy {len(list_data)} bài.\n")

    main_url = url

    for i, data in enumerate(list_data, 1):
        print(f"--- Bài {i}/{len(list_data)}: {data['title']}, {data['url']}")

        try:
            time.sleep(delay)
            driver.get(data["url"])

            # Chờ nội dung chính
            WebDriverWait(driver, 20).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "article"))
            )

            # ========= LẤY TEXT QUAN TRỌNG ==============
            strong_contents = driver.find_elements(By.CSS_SELECTOR, "article strong")
            print(f"  * Có {len(strong_contents)} đoạn strong:")
            for s in strong_contents:
                print("     ->", s.text.strip())

            # ========= LẤY ẢNH =============
            # 1. Ảnh slideshow
            slide_imgs = driver.find_elements(
                By.CSS_SELECTOR,
                "picture img"
            )

            print(f"  * Slideshow/ảnh thường: {len(slide_imgs)} ảnh")

            for img in slide_imgs:
                src = img.get_attribute("src") or img.get_attribute("data-src")
                if src and not src.startswith("data:image"):
                    print("     ->", src)

            driver.get(main_url)

        except Exception as e:
            print(f"!!! Lỗi xử lý bài: {e}")
            driver.get(main_url)

    driver.quit()

except Exception as e:
    print("Lỗi:", e)
