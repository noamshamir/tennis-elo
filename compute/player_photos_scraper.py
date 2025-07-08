from selenium import webdriver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import time

db = []

url = "https://www.tennis.com/players-rankings/"

driver = webdriver.Firefox()
driver.implicitly_wait(10)
driver.get(url)

for i in range(7):
    try:
        load_more = driver.find_element(By.CLASS_NAME, "fa-button.-read-more")
        load_more.click()
        time.sleep(1)
    except:
        break

rows = driver.find_elements(By.CSS_SELECTOR, ".d3-l-col__col-12.tc-players-rankings__players")
# print(f'Rows: {rows}')

for row in rows:
    soup = BeautifulSoup(row.get_attribute("outerHTML"), "html.parser")
    img_tag = soup.find("img")
    
    img_src = img_tag.get("src")
    img_alt = img_tag.get("alt")
    db.append({
        img_alt: img_src,
    })

driver.quit()

print(db)