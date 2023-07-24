import time
import json
import re
import pandas as pd
from flask import Flask, jsonify
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc
from selenium import webdriver

def get_chrome_driver():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--window-size=1920,1080')
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def is_element_exists(driver, by, element):
    try:
        driver.find_element(
            by, element)
        return True
    except:
        return False


def custom_call(user_input):
    driver = get_chrome_driver()
    vehicle_urls = []
    final_payload = []
    base_url = "https://www.copart.com/"
    driver.get(base_url)
    time.sleep(2)

    if is_element_exists(driver, By.CSS_SELECTOR,"#input-search"):
        driver.find_element(By.CSS_SELECTOR,"#input-search").send_keys(user_input)
    if is_element_exists(driver,By.CSS_SELECTOR,"button[aria-label='Search Inventory']"):
        driver.execute_script("arguments[0].click();", WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label='Search Inventory']"))))
    time.sleep(3)
    if is_element_exists(driver, By.XPATH, "(//a[@class='cprt-btn-yellow-content search_result_btn'])"):
        vehicle_links = driver.find_elements(By.XPATH, "(//a[@class='cprt-btn-yellow-content search_result_btn'])")
        for span in vehicle_links:
            href = span.get_attribute("href")
            if href not in vehicle_urls:
                vehicle_urls.append(href)
        if len(vehicle_urls) > 5:
            vehicle_urls = vehicle_urls[0:5]
    print(vehicle_urls)
    for url in vehicle_urls:
        try:
            print("\nLink: ", url)
            driver.get(url)
            time.sleep(5)
            title = vin_number = color = odometer =year = make =  model = vehicle_type = ""
            vehicle_value = 0
            image_urls = []

            #Name of vehicle
            if is_element_exists(driver, By.CSS_SELECTOR, ".title-and-highlights h1"):
                title = driver.find_element(By.CSS_SELECTOR, ".title-and-highlights h1").text
            #print("title: ", title)

            #year + make + model
            if title:
                year = re.findall(r'\b\d{4}\b', title)[0]
                make = title.split(' ', 1)[1].split(' ', 1)[0]
                model = title.split(' ', 2)[2]
            #print(f"Year: {year}, Make: {make}, Model: {model}")

            #estimated value of the vehicle
            if is_element_exists(driver, By.CSS_SELECTOR,"span[data-uname='lotdetailEstimatedretailvalue']"):
                value = driver.find_element(By.CSS_SELECTOR, "span[data-uname='lotdetailEstimatedretailvalue']").text.replace(",","").replace("$","").strip()
                vehicle_value = re.findall(r'\d+',value)
                if vehicle_value:
                    vehicle_value = int(vehicle_value[0])
                else:
                    vehicle_value = 0
            #print(f"Prices--> value: {vehicle_value}")

            #vin of the vehicle
            if is_element_exists(driver,By.CSS_SELECTOR,"#vinDiv"):
                vin_number = driver.find_element(By.CSS_SELECTOR, "#vinDiv").text.replace("*","")
            #print("vin number",vin_number)

            #color of the vehicle
            if is_element_exists(driver,By.CSS_SELECTOR,"span[data-uname='lotdetailColorvalue']"):
                color = driver.find_element(By.CSS_SELECTOR, "span[data-uname='lotdetailColorvalue']").text
            #print("color",color)

            #odometer of the vehicle
            if is_element_exists(driver,By.XPATH,"(//span[@class='bold d-flex j-c_s-b']//span)[2]"):
                odometer = driver.find_element(By.XPATH, "(//span[@class='bold d-flex j-c_s-b']//span)[2]").text
            #print("odometer",odometer)
            
            #type of the vehicle
            if is_element_exists(driver,By.CSS_SELECTOR,"span[data-uname='lotdetailvehicletype']"):
                vehicle_type = driver.find_element(By.CSS_SELECTOR,"span[data-uname='lotdetailvehicletype']").text
            #print("vehicle type",vehicle_type)

            #Images of vehicle
            if is_element_exists(driver,By.XPATH,"(//div[@class='spZoomViewer']//img)"):
                images = driver.find_elements(By.XPATH, "(//div[@class='spZoomViewer']//img)")
                for image in images:
                    scr_of_image = image.get_attribute("full-url")
                    if scr_of_image not in image_urls and scr_of_image is not None:
                        image_urls.append(scr_of_image)
            #print("Images of vehicle",image_urls)

            payload = []
            payload.append(url.replace("'",""))
            payload.append(title)
            payload.append(year)
            payload.append(make)
            payload.append(model)
            payload.append(vehicle_value)
            payload.append(vin_number)
            payload.append(color)
            payload.append(odometer)
            payload.append(vehicle_type)
            payload.append(json.dumps(image_urls))
            #print(payload)
            
            final_payload.append(payload)
            print("Data inserted into the final_payload file successfully.")

        except Exception as e:
            pass
    driver.close()
    return final_payload


app = Flask(__name__)
df1 = pd.read_csv('part1.csv')
df2 = pd.read_csv('part2.csv')
frames = [df1, df2]
df = pd.concat(frames)
@app.route('/<title>', methods=['GET'])

def get_vehicle_data(title):
    filtered_df = df[df['Title'].str.contains(title, case=False, na=False)]
    if filtered_df.empty:
        custom_data = custom_call(title)
        return jsonify(custom_data)
        #return jsonify({'error': 'No matching vehicles found'}), 404
    data = filtered_df.to_dict(orient='records')
    return jsonify(data)
if __name__ == '__main__':
    app.run(host="0.0.0.0",port=5000,debug=True)

