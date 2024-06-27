import requests
from bs4 import BeautifulSoup
import re
import pyodbc

class color:
   GREEN = '\033[92m'
   YELLOW = '\033[93m'
   RED = '\033[91m'
   BOLD = '\033[1m'
   UNDERLINE = '\033[4m'
   END = '\033[0m'

units = ["GB", "TB", "MB"]

try:
   conn = pyodbc.connect(r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=.\DATABASE\Inventory.accdb;')
   print(f"{color.BOLD}{color.GREEN}Connected To Database {color.END} {color.END}")
   cursor = conn.cursor()
except pyodbc.Error as e:
   print("Error in Connection", e)
    
while True:
   model_number = input(f'{color.BOLD}Scan the model number>> {color.END}')

   url = f"https://hddfaqs.com/?s={model_number}"

   # ###############################################################
   # ####### WORKING FOR SEAGATE AND TOSHIBA AND EVERYTHING ########
   # ###############################################################
   print(url)

   try:
      req = requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36'})

      soup = BeautifulSoup(req.text, 'html.parser')

      try:
         url = soup.find('article').find_all('a')[0].get("href")
      except:
         print(f"{color.BOLD}{color.RED}This disk doesn't exist {color.END}{color.END}")
         continue

      print(f"{color.BOLD}Changed URL to :{color.END} {url}")

      req = requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36'})

      soup = BeautifulSoup(req.text, 'html.parser')

      ############################################
      ########### CAPACITY #######################
      ############################################
      try:
         capacity_text = str(soup.find("article").find("li", string=lambda text: text and text.startswith('Capacity: ')).text)
         capacity = capacity_text.split()[1:2][0]
         capacity_unit = str(soup.find("article").find("li", string=lambda text: text and text.startswith('Capacity: ')).text).split()[2:3][0]
      except:
         storage_capacity_element = soup.find("strong", string=lambda text: text and text.startswith('Storage Capacity: '))
         capacity_text = storage_capacity_element.find_next('li')
         capacity_text = capacity_text.find_previous('li').text.split()[-1]

         capacity = "".join(filter(str.isdigit, capacity_text))
         capacity_unit = "".join(filter(str.isalpha, capacity_text))

      match capacity_unit:
         case "TB":
            capacity = int(capacity)*1000
         case "MB":
            capacity = int(capacity)/1000
         case _:
            pass

      #########################################
      ####### BRAND ###########################
      #########################################
      try:
         manufacturer = str(soup.find("article").find("li", string=lambda text: text and text.startswith('Manufacturer: ')).text).split()[1:][0]
      except:
         manu_element = soup.find("strong", string=lambda text: text and text.startswith('Manufacturer: '))
         try:
            manufacturer = manu_element.find_next('li')
            manufacturer = manufacturer.find_previous('li').text.split()[-1]
         except:
            manufacturer = manu_element.find_previous('li')
            manufacturer = manufacturer.find_next('li').text.split()[-1]

      #########################################
      ####### SIZE ############################
      #########################################
      try:
         size = str(soup.find("article").find("li", string=lambda text: text and text.startswith('Form Factor: ')).text)
         size = re.findall(r"\d+\.\d+", size)[0]
      except:
         size_element = soup.find("strong", string=lambda text: text and text.startswith('Form Factor: '))
         try:
            size = size_element.find_next('li')
            size = size.find_previous('li').text
         except:
            size = size_element.find_previous('li')
            size = size.find_next('li').text

         size = re.findall(r"\d+\.\d+", size)[0]

      ##########################################
      ################## CACHE #################
      ##########################################
      desc = str(soup.select_one('.des1'))
      pattern = r"(\d+)MB Cache"
      match = re.search(pattern, desc)
      try:
         cache = match.group(1)
      except:
         cache = ""

      #########################################
      ############# INTERFACE #################
      #########################################
      try:
         interface = str(soup.find("article").find("li", string=lambda text: text and text.startswith('Disk Interface: ')).text).split()[2:][0]
         # Chosing the part before the "/"
         interface = interface.split("/")[0]
      except:
         interface_element = soup.find("strong", string=lambda text: text and text.startswith('Drive Interface: '))
         try:
            interface = interface_element.find_next('li')
            interface = interface.find_previous('li').text
         except:
            interface = interface_element.find_previous('li')
            interface = interface.find_next('li').text

         # Chosing the part before the "/"
         interface = interface.split("/")[0]

      match interface:
         case "Serial-ATA":
            interface = "SATA"
         case "Ultra-ATA":
            interface = "IDE"
         case "ATA":
            interface = "IDE"
         case _:
            pass

      serial_number = input(f'{color.BOLD}{color.YELLOW}Scan the serial number (Enter if no)>> {color.END}{color.END}')
      date = str(input(f'{color.BOLD}{color.YELLOW}Enter the date (Enter if no)>> {color.END}{color.END}'))
      country = input(f'{color.BOLD}{color.YELLOW}Enter the country (Enter if no)>> {color.END}{color.END}')
      location = input(f'{color.BOLD}{color.YELLOW}Enter the location (Enter if no)>> {color.END}{color.END}')

      disk_infos = {
         "model_number":model_number,
         "Manufacturer":manufacturer,
         "disk_capacity":capacity,
         "size":size,
         "serial_number":serial_number,
         "cache":cache,
         "date":date,
         "country":country,
         "disk_interface":interface,
         "type":type,
         "location":location
      }
         
      print(f'{color.BOLD}{color.RED}Model number :{color.END}{color.END} {model_number}')
      print(f'{color.BOLD}{color.RED}Manufacturer :{color.END}{color.END} {manufacturer}')
      print(f'{color.BOLD}{color.RED}Disk capacity :{color.END}{color.END} {capacity}GB')
      print(f'{color.BOLD}{color.RED}Size :{color.END}{color.END} {size}"')
      print(f'{color.BOLD}{color.RED}Serial number :{color.END}{color.END} {serial_number}')
      print(f'{color.BOLD}{color.RED}Cache :{color.END}{color.END} {cache}MB')
      print(f'{color.BOLD}{color.RED}Date :{color.END}{color.END} {date}')
      print(f'{color.BOLD}{color.RED}Country :{color.END}{color.END} {country}')
      print(f'{color.BOLD}{color.RED}Disk interface :{color.END}{color.END} {interface}')
      print(f'{color.BOLD}{color.RED}Type :{color.END}{color.END} HDD')
      print(f'{color.BOLD}{color.RED}Location :{color.END}{color.END} {location}')

      ok = str(input(f"{color.BOLD}Are the values OK ({color.GREEN}y{color.END}/{color.RED}n{color.END})?{color.END}")).lower()
      if(ok == "y"):
         pass
      elif(ok == "n"):
         capacity = input(f'{color.BOLD}{color.YELLOW}Enter disk capacity (GB)>> {color.END}{color.END}')
         manufacturer = input(f'{color.BOLD}{color.YELLOW}Enter manufacturer>> {color.END}{color.END}')
      else:
         continue

      sql = 'INSERT INTO DRIVES(Model_Number, Brand, Storage_in_GB, Size, Serial_Number, Cache, [Date], Country, Interface, Type, Location) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
      datas = model_number, manufacturer, int(capacity), size, serial_number, cache, date, country, interface, "HDD", location

      cursor.execute(sql, datas)
      cursor.commit()
      
      print(f"{color.BOLD}{color.GREEN}DRIVE {model_number} WAS ADDED TO THE DATABASE {color.END} {color.END}")
      
   except Exception as e:
      print(f'Error... :{e}')

   print("="*50)