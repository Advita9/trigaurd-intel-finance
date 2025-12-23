from playwright.sync_api import sync_playwright

class PlaywrightEngine:
    def __init__(self):
        self.browser = None
        self.page = None

    def launch(self):
        p = sync_playwright().start()
        self.browser = p.chromium.launch(headless=False)
        self.page = self.browser.new_page()
        return self.page

    def navigate(self, url: str):
        self.page.goto(url, wait_until="networkidle")

    def click(self, selector: str):
        self.page.wait_for_selector(selector)
        self.page.click(selector)

    def type_text(self, selector: str, text: str):
        self.page.wait_for_selector(selector)
        self.page.fill(selector, str(text))

    def screenshot(self) -> bytes:
        return self.page.screenshot()
    

    def selector_exists(self, selector: str) -> bool:
        try:
            self.page.wait_for_selector(selector, timeout=1000)
            return True
        except:
            return False
    def type_slow(self, selector: str, text: str):
        self.page.wait_for_selector(selector)
        self.page.click(selector)
        self.page.type(selector, text, delay=50)
    def select(self, selector: str, value: str):
        self.page.wait_for_selector(selector)
        self.page.select_option(selector, value=value)



