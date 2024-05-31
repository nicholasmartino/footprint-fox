import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

option = webdriver.ChromeOptions()
wd = webdriver.Chrome(executable_path="D:/chromedriver.exe", chrome_options=option)
wd.get("https://governmentofbc.maps.arcgis.com/apps/MapSeries/index.html?appid=d06b37979b0c4709b7fcf2a1ed458e03")
time.sleep(2)

# Click on 'Discovery and Download' button
buttons = wd.find_elements_by_class_name("entryLbl")
i = [b.text for b in buttons].index('Discovery and Download')
buttons[i].click()
time.sleep(4)

# Close pop-up window
wd.switch_to.frame(wd.find_elements_by_tag_name("iframe")[1])
wd.find_element_by_class_name("jimu-btn").click()

# Open attribute table
wd.find_element_by_class_name("jimu-widget-attributetable-switch").click()
time.sleep(1)

# Remove filter by map extent
wd.find_element_by_id("dijit_form_ToggleButton_0_label").click()

# Get DSM table
grid = wd.find_element_by_id("dgrid_0")

from requests_xml import XMLSession
session = XMLSession()

response = session.get('https://nrs.objectstore.gov.bc.ca/gdwuts')
tree = xml.etree.ElementTree.fromstring(response.content)


import requests

"bc_082e004_1_1_1_cyes_12_utm11_2018.laz"
"bc_092j056_1_1_3_xyes_8_utm10_20170601_dsm.laz"

"bc_082g052_4_4_2_xli_12_utm11_2018_dsm"
"bc_082f004_2_1_2_xli_12_utm11_2018_dsm"
"bc_092g024_4_1_1_xyes_8_utm10_20170601_dsm"
"bc_092j056_1_1_3_xyes_8_utm10_20170601_dsm"
"bc_082l055_3_1_1_cyes_12_utm11_2018"
"bc_092h089_2_4_3_cyes_12_utm11_2019"


