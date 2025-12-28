from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

class WeChatArticleExtractor:

    def extract_article_content(self, article_url):
        """提取公众号文章内容"""

        options = webdriver.SafariOptions()

        driver = webdriver.Safari(options=options)

        try:
            driver.get(article_url)
            # 等待页面加载完成
            time.sleep(3)

            # 等待特定元素出现
            wait = WebDriverWait(driver, 10)
            article = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#js_content"))
            )

            # 获取文章内容
            content = article.text

            return content

        finally:
            driver.quit()