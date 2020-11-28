from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time
import selenium
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

URL = "https://maketext.io/"

def main():
    print("Hello world")

    driver = webdriver.Firefox()
    driver.get(URL)
    print(driver.title)
    assert "maketext" in driver.title
    elem = driver.find_element_by_xpath("//div[@data-type='hole']")
    # print(elem.is_displayed())
    # print(elem.is_enabled())
    # print(elem)
    driver.execute_script("arguments[0].style.visibility = 'visible';",elem)
    elem.click()
    time.sleep(1)



    elem1 = driver.find_element_by_name("background")
    driver.execute_script("arguments[0].style.visibility = 'visible';",elem1)
    elem1.click()
    # none_elem = driver.find_element_by_class_name("ldcp-color-none")
    none_elem = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, "//div[@class='ldcp-color-none']")))

    # driver.find_element_by_xpath("//div[@class='ldcp-color-none']")
    # driver.execute_script("arguments[0].style.visibility = 'visible';",none_elem)
    # time.sleep(1)
    none_elem.click()
    # elem1.send_keys(Keys.LEFT_CONTROL, "A")
    # elem1.send_keys(Keys.BACKSPACE)
    # elem1.send_keys("none")
    # elem1.send_keys(Keys.ENTER)
    # elem1.send_keys(Keys.ESCAPE)
    # print(elem1)
    # ldcp-color-none
    # driver.implicitly_wait(1)
    time.sleep(1)



    # shadow = driver.find_element_by_name("shadow")
    # driver.execute_script("arguments[0].style.visibility = 'visible';",shadow)
    # shadow.click()
    # shadow.send_keys(Keys.LEFT_CONTROL, "A")
    # shadow.send_keys(Keys.BACKSPACE)
    # shadow.send_keys("none")
    # shadow.send_keys(Keys.ESCAPE)
    # # driver.implicitly_wait(1)
    # time.sleep(1)
    # print(elem1)

    # fill = driver.find_element_by_name("fill")
    # driver.execute_script("arguments[0].style.visibility = 'visible';",fill)
    # fill.click()
    # fill.send_keys(Keys.LEFT_CONTROL, "A")
    # fill.send_keys(Keys.BACKSPACE)
    # fill.send_keys("#000000")
    # fill.send_keys(Keys.ESCAPE)
    # driver.implicitly_wait(1)

    # elem.clear()
    time.sleep(5)
    # elem.send_keys("pycon")
    # elem.send_keys(Keys.RETURN)
    # assert "No results found." not in driver.page_source
    driver.close()


if __name__ == '__main__':
    main()