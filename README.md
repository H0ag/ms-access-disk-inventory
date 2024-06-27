# DOCUMENTATION upload.py
This **python** script adds information on physical disks to a Microsoft Access database. The information is automatically retrieved from **hddfaqs.com**, using the model number of the disks scanned by the user.

The database is stored in `.\DATABASE\Inventory.accdb`

To use the script you have to install :
- Microsoft Access
- Python

The python architecture **must** be the same as that of Microsoft Access.
- Python **x64** <--> MS access **x64**
- Python **x86** <--> MS access **x86**

## Microsoft Access database structure
TABLE NAME : **DRIVES**
| Column | Type |
|--------|------|
| ID_Drives | AutoIncrement |
| Model_Number | ShortText |
| Brand | ShortText |
| Storage_in_GB | Number |
| Size | ShortText |
| Serial_Number | LongText |
| Cache | ShortText |
| Date | ShortText |
| Country | ShortText |
| Tested | Yes/No |
| Interface | ShortText |
| Working | Yes/No |
| Label_notes | LongText |
| Miscelanious | LongText |
| Location | ShortText |

```sql
CREATE TABLE DRIVES (
    ID_Drives AUTOINCREMENT PRIMARY KEY,
    Model_Number SHORT TEXT,
    Brand SHORT TEXT,
    Storage_in_GB NUMBER,
    Size SHORT TEXT,
    Serial_Number LONG TEXT,
    Cache SHORT TEXT,
    Date SHORT TEXT,
    Country SHORT TEXT,
    Tested YESNO,
    Interface SHORT TEXT,
    Working YESNO,
    Label_notes LONG TEXT,
    Miscelanious LONG TEXT,
    Location SHORT TEXT
);
```

## Libraries :
```python
import requests
from bs4 import BeautifulSoup
import re
import pyodbc
```

| Library | Usage |
|---------|----------|
| Requests | to fetch the datas from **hddfaqs.com** |
| BeautifulSoup | to parse the HTML page |
| re | to search and manipulate strings |
| pyodbc | for connection to the Microsoft Access database |

### You can install the libraries using the requirements.txt
```bash
pip install -r requirements.txt
```

## Script logic
For the moment, **hddfaqs** doesn't offer an API for data retrieval. The script uses a WebScrapping technique, which consists in extracting the HTML elements of a page, and then retrieving the raw values.

To find the right drive, the script uses the search system to find the first result, then visits the new page for the data.

### Try to connect to the database using the pyodbc library
```python
try:
   conn = pyodbc.connect(r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=.\DATABASE\Inventory.accdb;')
   print(f"{color.BOLD}{color.GREEN}Connected To Database {color.END} {color.END}")
   cursor = conn.cursor()
except pyodbc.Error as e:
   print("Error in Connection", e)
```
------------------
### Main loop
```python
while True:
    #### ASK THE USER TO SCAN A DRIVE ####
    model_number = input(f'{color.BOLD}Scan the model number>> {color.END}')
```
**Now the URL is:** https://hddfaqs.com/?s= + model_number

Then, the script tries out the entire script in safe mode. If there's an error somewhere, it displays the error but doesn't stop the script.

```python
try:
    #### SCRIPT ####
except Exception as e:
    print("Error: ", e)
```

Still in safe mode, the script is using the **requests** lib to fetch the URL.
In the headers, we specify a user-agent to make the platform believe that we are an ordinary user.
```python
req = requests.get(url, headers={'User-Agent': 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36'})
```
In the result, the script attempts to obtain the first element. If it fails to do so, this means that the disk is not in the database, which interrupts the loop.

```python
try:
    url = soup.find('article').find_all('a')[0].get("href")
except:
    print(f"{color.BOLD}{color.RED}This disk doesn't exist {color.END}{color.END}")
    continue
```

If successful, the URL has been modified by the url of the first element. The script retrieves the new page.

---
**Retrieving disk information :**

**CAPACITY :**

```python
# Finds the <li> element in <article> with content that starts with "Capacity: "
capacity_text = str(soup.find("article").find("li", string=lambda text: text and text.startswith('Capacity: ')).text)
# Gets the value
capacity = capacity_text.split()[1:2][0]
# Gets the unit (TB, GB, MB)
capacity_unit = str(soup.find("article").find("li", string=lambda text: text and text.startswith('Capacity: ')).text).split()[2:3][0]
```
Sometimes on **hddfaqs** it can't work because on some pages the text is written with `Ex: <li><strong>Storage Capacity: </strong>128 GB</li>` and not `Ex: <li>Capacity: 128GB</li>` so the script can't read the value with this method. That's why it uses safe mode for this, because if it doesn't work, we try the second method, and if it still doesn't work, error...

so here is the second method :
```python
# Finds the element "Storage Capacity".
storage_capacity_element = soup.find("strong", string=lambda text: text and text.startswith('Storage Capacity: '))
# Selects the next element
capacity_text = storage_capacity_element.find_next('li')
# Select the previous one
capacity_text = capacity_text.find_previous('li').text.split()[-1]

# Parse the content (Digits=Drive_Capacity | alpha=Drive_Unit)
capacity = "".join(filter(str.isdigit, capacity_text))
capacity_unit = "".join(filter(str.isalpha, capacity_text))
```

The script needs the capacity unit beacause on some drives the values can switch between GB, TB, MB. And in the database we only want GB, so we have to convert the value :

```python
# Switch statement
match capacity_unit:
    # If capacity unit is TB so we multiply the value by 1000
    case "TB":
        capacity = int(capacity)*1000
    # If capacity unit is MB so we divide the value by 1000
    case "MB":
        capacity = int(capacity)/1000
    # Else it's already in GB we can ignore it
    case _:
        pass
```

**BRAND :**

For the brand this is the same way, first it tries to find an element like `<li>Manufacturer: Toshiba</li>`
```python
manufacturer = str(soup.find("article").find("li", string=lambda text: text and text.startswith('Manufacturer: ')).text).split()[1:][0]
```
If it can't it tries to find a `<strong>` element, select the next one, then the previous one.
```python
manu_element = soup.find("strong", string=lambda text: text and text.startswith('Manufacturer: '))
try:
    manufacturer = manu_element.find_next('li')
    manufacturer = manufacturer.find_previous('li').text.split()[-1]
except:
    manufacturer = manu_element.find_previous('li')
    manufacturer = manufacturer.find_next('li').text.split()[-1]
```

**SIZE :**

Same method as **BRAND**

**CACHE :**

Finding the disk cache is a different method. The script selects the disk description "**.desc1**" because the cache is somewhere in the description. It therefore uses the **re** library to find the text "**MB Cache**". We then analyze the value just before it. If it finds something, we have the cache, otherwise the cache won't be in the database.

```python
desc = str(soup.select_one('.des1'))
pattern = r"(\d+)MB Cache"
match = re.search(pattern, desc)
try:
    cache = match.group(1)
except:
    cache = ""
```

**INTERFACE :**

Finding the interface is the same method as **BRAND** and **CACHE**.

Some results have to be converted.
```python
match interface:
    # If interface is "Serial-ATA" it will be "SATA"
    case "Serial-ATA":
        interface = "SATA"
    # If interface is "Ultra-ATA" it will be "IDE"
    case "Ultra-ATA":
        interface = "IDE"
    # If interface is "ATA" it will be "IDE"
    case "ATA":
        interface = "IDE"
    # Else it skips
    case _:
        pass
```

The script can't find certain information on its own using hddfaqs, such as serial number or date, country, location. It therefore asks the user to provide this information using the :

```python
serial_number = input(f'{color.BOLD}{color.YELLOW}Scan the serial number (Enter if no)>> {color.END}{color.END}')
date = str(input(f'{color.BOLD}{color.YELLOW}Enter the date (Enter if no)>> {color.END}{color.END}'))
country = input(f'{color.BOLD}{color.YELLOW}Enter the country (Enter if no)>> {color.END}{color.END}')
location = input(f'{color.BOLD}{color.YELLOW}Enter the location (Enter if no)>> {color.END}{color.END}')
```

### Finishing :
Finally, it displays all the drive information to the user. If all values are correct, it adds the drive to the database. If not, it requests the correct capacity and manufacturer.

**Adding the drive to the database:**

SQL command :
```sql
INSERT INTO DRIVES(Model_Number, Brand, Storage_in_GB, Size, Serial_Number, Cache, [Date], Country, Interface, Type, Location) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
```

## Credits
Made by [h0ag](https://github.com/h0ag/) for [Computer Doctor](https://maps.app.goo.gl/t44tc7LGPzBF97ndA)