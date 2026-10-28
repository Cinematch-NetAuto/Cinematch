import time
import uuid
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

def run_e2e_tests():
    service = Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    # options.add_argument('--headless')
    driver = webdriver.Chrome(service=service, options=options)
    wait = WebDriverWait(driver, 10)

    test_email = f"testuser_{uuid.uuid4().hex[:8]}@example.com"
    test_password = "SecurePassword123!"

    # --- Test Reporting Statistics ---
    TOTAL_TESTS = 8
    passed_tests = 0
    failure_reason = None

    try:
        print("Starting End-to-End Test Suite...\n")

        # ==========================================
        # PHASE 1a: NEGATIVE REGISTRATION
        # ==========================================
        print("1/8. Testing negative registration (validation errors)...")
        driver.get("http://localhost:5173/register")
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[autoComplete='nickname']"))).send_keys("Test User")
        driver.find_element(By.CSS_SELECTOR, "input[type='email']").send_keys(test_email)
        driver.find_element(By.CSS_SELECTOR, "input[type='password']").send_keys("short")
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        
        wait.until(EC.presence_of_element_located((By.ID, "password-problem")))
        wait.until(EC.presence_of_element_located((By.XPATH, "//span[contains(text(), 'Choose at least 3 genres')]")))
        print("✅ Passed: Caught invalid inputs.")
        passed_tests += 1
        driver.refresh()

        # ==========================================
        # PHASE 1b: SUCCESSFUL REGISTRATION
        # ==========================================
        print(f"2/8. Registering new user: {test_email}")
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[autoComplete='nickname']"))).send_keys("Test Automation")
        driver.find_element(By.CSS_SELECTOR, "input[type='email']").send_keys(test_email)
        driver.find_element(By.CSS_SELECTOR, "input[type='password']").send_keys(test_password)

        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".tiles")))
        genre_buttons = driver.find_elements(By.CSS_SELECTOR, "button.tile")
        for i in range(3):
            genre_buttons[i].click()
            time.sleep(0.5) 
            
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        wait.until(EC.url_to_be("http://localhost:5173/"))
        print("✅ Passed: Registration successful.")
        passed_tests += 1

        # ==========================================
        # PHASE 2: SEARCH FEATURE
        # ==========================================
        print("3/8. Testing Movie Search feature...")
        driver.get("http://localhost:5173/search")
        search_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='search']")))
        search_input.send_keys("Inception")
        search_input.send_keys(Keys.RETURN)
        
        results = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".movie-card")))
        assert len(results) > 0
        print(f"✅ Passed: Found {len(results)} search results.")
        passed_tests += 1

        # ==========================================
        # PHASE 3: AUTHENTICATED FEATURES 
        # ==========================================
        print("4/8. Testing Recommendations (Protected)...")
        driver.get("http://localhost:5173/me/recommendations")
        wait.until(EC.url_contains("/me/recommendations"))
        rec_items = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".movie-card")))
        assert len(rec_items) > 0
        print("✅ Passed: Recommendations loaded.")
        passed_tests += 1

        print("5/8. Testing Library & Preferences Navigation...")
        driver.get("http://localhost:5173/me/library")
        wait.until(EC.url_contains("/me/library"))
        driver.get("http://localhost:5173/me/preferences")
        wait.until(EC.url_contains("/me/preferences"))
        print("✅ Passed: Authenticated navigation functional.")
        passed_tests += 1

        # ==========================================
        # PHASE 4: LOGOUT & ROUTE ENFORCEMENT
        # ==========================================
        print("6/8. Testing logout & protected route enforcement...")
        driver.execute_script("window.localStorage.removeItem('cinematch.token');")
        driver.get("http://localhost:5173/me/recommendations")
        wait.until(EC.url_contains("/login"))
        print("✅ Passed: Kicked out unauthenticated user.")
        passed_tests += 1

        # ==========================================
        # PHASE 5a: NEGATIVE LOGIN
        # ==========================================
        print("7/8. Testing negative login (wrong password)...")
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email']"))).send_keys(test_email)
        driver.find_element(By.CSS_SELECTOR, "input[type='password']").send_keys("WrongPassword123!")
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

        error_message = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".form-error")))
        assert error_message is not None
        print("✅ Passed: Invalid login rejected.")
        passed_tests += 1
        driver.refresh()

        # ==========================================
        # PHASE 5b: SUCCESSFUL RE-AUTHENTICATION
        # ==========================================
        print("8/8. Testing returning user login...")
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email']"))).send_keys(test_email)
        driver.find_element(By.CSS_SELECTOR, "input[type='password']").send_keys(test_password)
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

        wait.until(EC.url_to_be("http://localhost:5173/"))
        print("✅ Passed: Returning user authenticated.")
        passed_tests += 1

    except Exception as e:
        failure_reason = str(e)
        driver.save_screenshot("test_failure.png")
        print("\nA test failed. Execution halted to preserve state.")
        
    finally:
        time.sleep(1)
        driver.quit()

        # --- Generate Test Report ---
        failed_tests = 1 if passed_tests < TOTAL_TESTS else 0
        skipped_tests = TOTAL_TESTS - passed_tests - failed_tests
        success_rate = (passed_tests / TOTAL_TESTS) * 100

        print("\n" + "="*45)
        print("CINEMATCH E2E TEST REPORT")
        print("="*45)
        print(f" Total Tests    : {TOTAL_TESTS}")
        print(f" Passed         : {passed_tests}")
        print(f" Failed         : {failed_tests}")
        print(f" Skipped        : {skipped_tests}")
        print(f" Success Rate   : {success_rate:.1f}%")
        print("="*45)
        
        if failure_reason:
            print(f"\n[FAILURE DETAILS]: \n{failure_reason}")
            print("\nScreenshot saved to: test_failure.png")
        else:
            print("\nAll tests passed successfully!")

if __name__ == "__main__":
    run_e2e_tests()