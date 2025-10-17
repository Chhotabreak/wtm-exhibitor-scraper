from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from bs4 import BeautifulSoup
import pandas as pd
import time

# --- Setup Chrome driver ---
options = Options()
options.add_argument("--start-maximized")
service = Service("path_to_chromedriver")  # 🔧 replace with your local path
driver = webdriver.Chrome(service=service, options=options)

url = "https://www.wtm.com/london/en-gb/exhibitor-directory.html#/"
driver.get(url)
time.sleep(10)  # wait for page to load

# --- Scroll until all exhibitors are loaded ---
last_height = driver.execute_script("return document.body.scrollHeight")
while True:
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(3)
    new_height = driver.execute_script("return document.body.scrollHeight")
    if new_height == last_height:
        break
    last_height = new_height

# --- Parse the page content ---
soup = BeautifulSoup(driver.page_source, "html.parser")

exhibitors = []
cards = soup.find_all("div", class_="wtm-exhibitor-card")  # adjust if needed

for card in cards:
    name = card.find("h3").get_text(strip=True) if card.find("h3") else None
    description = card.find("p").get_text(strip=True) if card.find("p") else None

    # Click to open detail (optional deeper scraping)
    try:
        elem = driver.find_element(By.XPATH, f"//h3[text()='{name}']")
        ActionChains(driver).move_to_element(elem).click().perform()
        time.sleep(2)
        detail_soup = BeautifulSoup(driver.page_source, "html.parser")

        why_visit = detail_soup.find("h2", string="Why Visit Our Stand")
        why_visit = why_visit.find_next("p").get_text(strip=True) if why_visit else None

        brands = detail_soup.find("h2", string="Brands We Will Feature")
        brands = brands.find_next("p").get_text(strip=True) if brands else None

        social_links = [a["href"] for a in detail_soup.find_all("a", href=True) if any(x in a["href"] for x in ["facebook", "linkedin", "instagram", "twitter"])]

        address = detail_soup.find("div", class_="exhibitor-address")
        address = address.get_text(" ", strip=True) if address else None

        products = [p.get_text(strip=True) for p in detail_soup.find_all("div", class_="product-name")]

        contact = detail_soup.find("div", class_="contact-details")
        contact = contact.get_text(" ", strip=True) if contact else None

        driver.back()
        time.sleep(2)

    except Exception as e:
        why_visit = brands = address = products = contact = None
        social_links = []

    exhibitors.append({
        "Company Name": name,
        "Description": description,
        "Why Visit Our Stand": why_visit,
        "Brands": brands,
        "Social Links": ", ".join(social_links),
        "Address": address,
        "Contact Info": contact,
        "Products": ", ".join(products) if products else None
    })

# --- Save to Excel ---
df = pd.DataFrame(exhibitors)
df.to_excel("wtm_exhibitors.xlsx", index=False)
print("✅ Data extraction complete! Saved as wtm_exhibitors.xlsx")

driver.quit()
