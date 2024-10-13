import os
import time
from PIL import Image
import re
import zipfile
import pandas as pd
import chardet
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import WebDriverException



def open_browser(url, download_directory):
    print(f"Opening browser with URL: {url} and download directory: {download_directory}")
    from selenium.webdriver.chrome.options import Options
    options = Options()
    # set download directory
    prefs = {
        "download.default_directory": download_directory,
        "profile.default_content_settings.popups": 0, 
        "profile.default_content_setting_values.automatic_downloads": 1  
    }
    options.add_experimental_option("prefs", prefs)
    driver = webdriver.Chrome(options=options)

    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        })
        """
    })

    driver.get(url)
    driver.implicitly_wait(3)
    time.sleep(1)

    return driver

def unzip_all_files(directory, extract_to):
    """
    Unzips all ZIP files in the specified directory and deletes them after extraction.
    
    :param directory: Path to the directory containing ZIP files
    :param extract_to: Directory where files should be extracted
    """
    for item in os.listdir(directory):
        if item.endswith(".zip"): 
            file_path = os.path.join(directory, item)
            try:
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_to)
                print(f"Unzipped: {file_path}")
                os.remove(file_path)
                print(f"Deleted: {file_path}")
            except zipfile.BadZipFile:
                print(f"Error: {file_path} is not a valid zip file.")

def get_latest_file_in_dir(directory):
    files = [os.path.join(directory, f) for f in os.listdir(directory)]
    files = [f for f in files if os.path.isfile(f)]
    if not files:
        return None
    return max(files, key=os.path.getmtime)

def download_file_from_each_country(driver, download_directory):
    rows = driver.find_elements(By.XPATH, "//tr[@align='center']")

    # iterate through each row of the table
    for row in rows:
        # print("00000000000")
        type_column = row.find_element(By.XPATH, ".//td[@id='Survey Type']")
        type_text = type_column.text

        if type_text == "Standard DHS":
            survey_link_element = row.find_element(By.XPATH, ".//td[@id='link to download Survey datasets']/a")

            driver.execute_script("window.open(arguments[0].href);", survey_link_element)
            time.sleep(1)
            driver.switch_to.window(driver.window_handles[-1])
            time.sleep(1)

            surveyTitle = driver.find_element(By.XPATH, "//div[@id='surveyTitle']").text
            cleaned_text = re.sub(r'[^\w\s-]', ' ', surveyTitle)
            cleaned_text = re.sub(r'\s+', ' ', cleaned_text)
            surveyTitle = cleaned_text.strip()
            print(surveyTitle)





            # first locate on the IR link
            ir_element = driver.find_element(By.XPATH, "//td[@id='IR']")

            # find all following tr elements
            parent_tr = ir_element.find_element(By.XPATH, "./ancestor::tr")
            sub_rows = parent_tr.find_elements(By.XPATH, "./following-sibling::tr")
            # print(f"Found {len(sub_rows)} sub_rows")

            for sub_row in sub_rows:
                try:
                    # find the first element that contains the text "Stata dataset"
                    first_matching_element = sub_row.find_element(By.XPATH, ".//td[contains(text(), 'Stata dataset')]")
                    print(first_matching_element.text)

                    if first_matching_element:
                        print(333)
                        checkbox_td = first_matching_element.find_element(By.XPATH, "./preceding-sibling::td[2]")
                        print(444)
                        
                        # get the latest file in the download directory
                        latest_file_before_download = get_latest_file_in_dir(download_directory)
                        
                        # download the file
                        IR_download_element = checkbox_td.find_element(By.XPATH, ".//a")
                        driver.execute_script("arguments[0].click();", IR_download_element)
                        print("Download started, waiting for completion...")

                        # wait for the file to be downloaded
                        new_file = None
                        while not new_file:
                            time.sleep(0.5) 
                            latest_file_after_download = get_latest_file_in_dir(download_directory)
                            if latest_file_after_download != latest_file_before_download:
                                new_file = latest_file_after_download

                        # make sure the file is fully downloaded
                        while new_file.endswith('.crdownload'):
                            time.sleep(1)
                            new_file = get_latest_file_in_dir(download_directory)
                    
                        print(f"New file downloaded: {new_file}")
                        
                        # construct the new file name
                        new_file_name = f"{surveyTitle}.zip"
                        new_file_path = os.path.join(download_directory, new_file_name)

                        print(f"Trying to rename: {new_file}")
                        print(f"New file name: {new_file_path}")

                        # check if the file already exists
                        if os.path.exists(new_file):
                            try:
                                os.rename(new_file, new_file_path)
                                print(f"File renamed to: {new_file_path}")
                            except Exception as e:
                                print(f"Failed to rename file: {e}")
                        else:
                            print(f"File not found: {new_file}")

                        break  # if the file is found, break out of the loop
                except:
                    print("No")
                    # if the element is not found,
                    continue

            


            try:
                # first locate on the IR link
                ir_element = driver.find_element(By.XPATH, "//td[@id='GE']")

                # find all following tr elements
                parent_tr = ir_element.find_element(By.XPATH, "./ancestor::tr")
                sub_rows = parent_tr.find_elements(By.XPATH, "./following-sibling::tr")
                # print(f"Found {len(sub_rows)} sub_rows")
                
                for sub_row in sub_rows:

                    try:
                        # Find the element that contains "Shape file (.shp)" text
                        shape_file_element = sub_row.find_element(By.XPATH, ".//td[contains(text(), 'Shape file (.shp)')]")
                        
                        if shape_file_element:
                            print("Found Shape file (.shp)")

                            # Locate the td element that is two preceding siblings before this element
                            preceding_td_element = shape_file_element.find_element(By.XPATH, "./preceding-sibling::td[2]")

                            # Locate the a element inside the preceding td element
                            download_link_element = preceding_td_element.find_element(By.XPATH, ".//a")

                            # Get the latest file in the download directory before download starts
                            latest_file_before_download = get_latest_file_in_dir(download_directory)

                            # Trigger the download by clicking the link
                            driver.execute_script("arguments[0].click();", download_link_element)
                            print("Download started, waiting for completion...")

                            # Wait for the file to be downloaded
                            new_file = None
                            while not new_file:
                                time.sleep(0.5)
                                latest_file_after_download = get_latest_file_in_dir(download_directory)
                                if latest_file_after_download != latest_file_before_download:
                                    new_file = latest_file_after_download

                            # Make sure the file is fully downloaded
                            while new_file.endswith('.crdownload'):
                                time.sleep(1)
                                new_file = get_latest_file_in_dir(download_directory)

                            print(f"New file downloaded: {new_file}")
                            
                            # Construct the new file name
                            new_file_name = f"{surveyTitle}_geo.zip"
                            new_file_path = os.path.join(download_directory, new_file_name)

                            print(f"Trying to rename: {new_file}")
                            print(f"New file name: {new_file_path}")

                            # Rename the file
                            if os.path.exists(new_file):
                                try:
                                    os.rename(new_file, new_file_path)
                                    print(f"File renamed to: {new_file_path}")
                                except Exception as e:
                                    print(f"Failed to rename file: {e}")
                            else:
                                print(f"File not found: {new_file}")

                            break  # Exit loop after successful download
                    except Exception as e:
                        print(f"Element not found or error: {e}")
                        continue            
            except NoSuchElementException:
                print("GE element not found, skipping download.")            



            
            
            
            driver.close()
            driver.switch_to.window(driver.window_handles[-1])

    time.sleep(1)        

def download_zip_dataFile(download_directory, login_account, password):

    url = 'https://dhsprogram.com/data/dataset_admin/login_main.cfm'
    driver = open_browser(url, download_directory)

    try:
        # login
        driver.find_element(By.CSS_SELECTOR, "#UserName").send_keys(login_account)
        driver.find_element(By.CSS_SELECTOR, "#Password").send_keys(password)
        driver.find_element(By.XPATH, "//input[@value='Sign In']").click()

        # select project
        driver.find_element(By.CSS_SELECTOR, 'select[name="proj_id"]').click()
        driver.find_element(By.CSS_SELECTOR, 'option[value="200228"]').click()
        driver.find_element(By.CSS_SELECTOR, 'select[name="Apr_Ctry_list_id"]').click()

        select_element = driver.find_element(By.CSS_SELECTOR, 'select[name="Apr_Ctry_list_id"]')
        select = Select(select_element)
        options_values = [option.get_attribute('value') for option in select.options][1:]

        for value in options_values:
            # select country
            driver.find_element(By.CSS_SELECTOR, f'option[value="{value}"]').click()

            # download file from each country
            download_file_from_each_country(driver, download_directory)

    except Exception as e:
        print(f"Error occurred in main process: {e}")
        time.sleep(999)

def unzip(directory):

    for filename in os.listdir(directory):
        if filename.endswith(".zip"):
            file_path = os.path.join(directory, filename)
            
            # get folder name
            folder_name = filename.replace(".zip", "")
            folder_path = os.path.join(directory, folder_name)

            # create folder if not exists
            os.makedirs(folder_path, exist_ok=True)
            
            # unzip file
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(folder_path)
            
            print(f"{filename} is unzipped in {folder_path}")

    print("All files are unzipped.")

def parse_do_file(file_path):
    labels_dict = {}

    # Detect the file encoding
    with open(file_path, 'rb') as file:
        result = chardet.detect(file.read())
        file_encoding = result['encoding']

    # Open the file with the detected encoding
    with open(file_path, 'r', encoding=file_encoding) as file:
        for line in file:
            if line.startswith('label variable'):
                parts = line.split()
                code = parts[2]  # The variable code, e.g., d130c
                label = ' '.join(parts[3:]).strip('"')  # The label, strip the quotes more cleanly
                labels_dict[code.upper()] = label  # Use upper case for consistency
    return labels_dict

def create_variable_description_csvFile(root_directory):

    # regex patterns
    item_pattern = r'^(\w+)\s+(.*?)\s+\d+\s+\d+\s+[AN]+\s+[IN]\s+\d+\s+\d+\s+[NoYes]+\s+[NoYes]+$'
    section_pattern = r'^-{5,}'

    # check file encoding
    def detect_file_encoding(file_path):
        with open(file_path, 'rb') as f:
            result = chardet.detect(f.read())
            return result['encoding']

    # iterate through all folders in the root directory
    for folder_name in os.listdir(root_directory):
        folder_path = os.path.join(root_directory, folder_name)
        
        print(f"handling...: {folder_name}")
        
        if os.path.isdir(folder_path):
            # find all map files in the folder
            for file_name in os.listdir(folder_path):
                if file_name.lower().endswith(".map"):
                    file_path = os.path.join(folder_path, file_name)
                    
                    print(f"handling...: {file_name}")
                    
                    # check file encoding
                    encoding = detect_file_encoding(file_path)
                    print(f"file encoding is: {encoding}")

                    data = []
                    section_count = 0
                    collect_data = False
                    previous_item = None

                    # read map file
                    with open(file_path, 'r', encoding=encoding) as file:
                        for line in file:
                            if re.match(section_pattern, line):
                                section_count += 1
                                if section_count == 4:
                                    collect_data = True
                                elif section_count == 5:
                                    collect_data = False
                                continue

                            if collect_data:
                                if previous_item:
                                    if line.strip().startswith('('):
                                        description_match = re.match(r'^\s*\((.*?)\)', line.strip())
                                        if description_match:
                                            description_content = description_match.group(1)
                                            if description_content.lower() == 'na':
                                                data.append(previous_item + ('na', 'Not applicable'))
                                            else:
                                                data.append(previous_item + ('NA', description_content))
                                            previous_item = None
                                            continue

                                    if line.strip() and re.match(r'^\s+[^\s]+$', line):
                                        description = line.strip()
                                        data.append(previous_item + ('NA', description))
                                        previous_item = None
                                        continue

                                    elif line.strip() and re.match(r'^\s+(\S+)\s+(.+)$', line):
                                        code_description = re.match(r'^\s+(\S+)\s+(.+)$', line)
                                        code = code_description.group(1)
                                        description = code_description.group(2).strip()
                                        data.append(previous_item + (code, description))
                                        continue
                                    else:
                                        data.append(previous_item + ('NA', 'NA'))
                                        previous_item = None

                                item_match = re.match(item_pattern, line)
                                if item_match:
                                    item_name = item_match.group(1)
                                    item_label = item_match.group(2).strip()
                                    previous_item = (item_name, item_label)

                    if previous_item:
                        data.append(previous_item + ('NA', 'NA'))

                    df = pd.DataFrame(data, columns=['Item Name', 'Item Label', 'Code', 'Description'])

                    item_counts = df['Item Name'].value_counts()
                    multiple_items = item_counts[item_counts > 1].index
                    df_multiple = df[df['Item Name'].isin(multiple_items)]
                    na_rows = df_multiple[(df_multiple['Code'] == 'NA') & (df_multiple['Description'] == 'NA')]
                    df_cleaned = df.drop(na_rows.index)
                    df_cleaned = df_cleaned[:-1]

                    # generate CSV file name
                    csv_file_name = f"{folder_name}_variable_description.csv"
                    csv_file_path = os.path.join(folder_path, csv_file_name)


                    # Find the .do file in the folder
                    do_file_path = None
                    for file_name in os.listdir(folder_path):
                        if file_name.lower().endswith(".do"):
                            do_file_path = os.path.join(folder_path, file_name)
                            break  # Assuming there is only one .do file per folder
                    
                    if do_file_path:
                        # Parse the .do file
                        labels_dict = parse_do_file(do_file_path)
                        df_cleaned['Item Label'] = df_cleaned['Item Name'].map(labels_dict)
                    else:
                        print(f"No .do file found in {folder_path}")

                    # save to CSV file
                    df_cleaned.to_csv(csv_file_path, index=False)
                    print(f"{csv_file_name} is saved to {folder_path}")

    print("All files are processed.")



if __name__ == "__main__":
    
    # set download directory, login account and password
    directory = 'E:\\Capstone_test'
    login_account = "yukileung523@gmail.com"
    password = "unimelbgroup25"

    download_zip_dataFile(directory, login_account, password)
    unzip(directory)
    create_variable_description_csvFile(directory)


