import time, unittest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE_URL = "http://127.0.0.1:5000"  

def wait_for(d, by, value, t=8):
    return WebDriverWait(d, t).until(EC.presence_of_element_located((by, value)))

class AuthUITest(unittest.TestCase):
    def setUp(self):
        self.d = webdriver.Chrome()
        self.d.maximize_window()

    def tearDown(self):
        self.d.quit()

    def test_register_then_login(self):
        d = self.d
        # --- Go to Register ---
        d.get(f"{BASE_URL}/register")
        if "Not Found" in d.page_source:
            d.get(f"{BASE_URL}/signup")

        # Unique email for each run
        email_val = f"ui{int(time.time())}@example.com"
        pwd_val = "test1234!"

        # --- Fill form (simple, common names/ids) ---
        # email (required)
        wait_for(d, By.CSS_SELECTOR, "input[name='email'], #email").send_keys(email_val)
        # password (required)
        wait_for(d, By.CSS_SELECTOR, "input[name='password'], #password").send_keys(pwd_val)
        # confirm password (optional)
        el = d.find_elements(By.CSS_SELECTOR, "input[name='confirm_password'], #confirm_password")
        if el: el[0].send_keys(pwd_val)
        # username (optional)
        el = d.find_elements(By.CSS_SELECTOR, "input[name='username'], #username")
        if el: el[0].send_keys("testuser_ui")
        # company (optional; tries multiple names/ids)
        el = d.find_elements(By.CSS_SELECTOR, "input[name='company'], #company, input[name='company_name'], #company_name, select[name='company'], select[name='company_name']")
        if el:
            tag = el[0].tag_name.lower()
            if tag == "select":
                el[0].send_keys("Aryal Tech")
            else:
                el[0].send_keys("Aryal Tech")

        # submit
        wait_for(d, By.CSS_SELECTOR, "button[type='submit'], input[type='submit']").click()
        time.sleep(1)

        # quick success check
        page = d.page_source.lower()
        self.assertTrue(any(k in page for k in [
            "registration successful", "registered successfully", "account created", "welcome", "logout"
        ]), "Registration didn’t show a success indicator.")

        # --- If not auto-logged-in, login ---
        if "logout" not in page:
            d.get(f"{BASE_URL}/login")
            if "Not Found" in d.page_source:
                d.get(f"{BASE_URL}/signin")

            wait_for(d, By.CSS_SELECTOR, "input[name='email'], #email").send_keys(email_val)
            wait_for(d, By.CSS_SELECTOR, "input[name='password'], #password").send_keys(pwd_val)
            wait_for(d, By.CSS_SELECTOR, "button[type='submit'], input[type='submit']").click()
            time.sleep(0.8)
            page = d.page_source.lower()

        self.assertTrue(any(k in page for k in ["welcome", "dashboard", "logout"]),
                        "Login didn’t show success indicators.")

if __name__ == "__main__":
    unittest.main(verbosity=2)
