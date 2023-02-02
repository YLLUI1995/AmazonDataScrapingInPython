## -----------------------------------------------------------------------------------------------------------------------
# This tool: 
#     1) Reads Amazon product urls from .csv file (file name in const_file_name_input_urls, as below). 
#     2) For each url, extracts the product data from Amazon website, save product info into prod_info_list.
#     3) Writes data from prod_info_list into output .csv file (file name in const_file_name_output_product_info_log, as below). 
## -----------------------------------------------------------------------------------------------------------------------

## ----- set run variables
const_request_headers = ({'User-Agent':
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US, en;q=0.5'})   #  http://httpbin.org/get

## -- name input csv file (with product urls)    
const_file_name_input_urls="amazon_product_urls.csv"  # Two columns: ProductURL, ProductShortName 

## -- name output csv file (with output product info)   
const_file_name_output_product_info_log="amazon_product_info_log.csv" # Eight columns: ProductID, ProductShortName, Price, DateTime, Rating, Error, URL, ProductLongName) 

## ----- referenced libraries
from dataclasses import dataclass
from bs4 import BeautifulSoup 
from datetime import datetime
import requests
import csv
from requests.api import head
import pathlib
import pandas as pd

## ----- class: ProductInfo 
@dataclass
class ProductInfo:
    id: str
    product_short_name: str
    price: str
    title: str
    rating: str
    current_date_time: str
    err_msg: str
    url: str
    def __init__(self, url: str, product_short_name: str, id: str, price: str, title: str, rating: str, err_msg: str):
        self.url = url
        self.product_short_name = product_short_name
        self.id = id
        self.price = price
        self.title = title
        self.rating = rating
        self.current_date_time = datetime.now().strftime("%m/%d/%Y %H:%M:%S")
        self.err_msg = err_msg

## ----- class: ProductInfoList 
class ProductInfoList :
    list: list
    def __init__(self):    
       self.list=[]  
    def append(self, prod: ProductInfo):
        self.list.append([prod.id, prod.product_short_name, prod.price, prod.current_date_time, prod.rating, prod.err_msg, prod.url, prod.title]) 


## ----- function: read csv file and return all of its rows
def ReadCSVFile(file_name: str) -> list: 
    rows = []
    file = open(file_name)
    csvreader = csv.reader(file)
    next(csvreader) # skip header    
    for row in csvreader:
        rows.append(row)
    file.close()
    return rows

## ----- function: write data rows to csv file
def WriteCSVFile(file_name: str, data_list: list, header_list: list):
    file = pathlib.Path(file_name)
    df = pd.DataFrame(data_list)
    if file.exists():
        df.to_csv(file_name, mode='a', index=False, header=False)
    else:
        df.to_csv(file_name, mode='w', index=False, header=header_list)
    try:
       file.close()
    except:
       pass

## ------ function: given url, scrap its data from Amazon website, return its info object
def GetProductInfoByAmazonURL(url: str, product_short_name: str) -> ProductInfo:
    prodInfo = ProductInfo(url, product_short_name, "", "", "", "", "")
    try:        
        webpage = requests.get(url, headers=const_request_headers)
        soup = BeautifulSoup(webpage.content, "html.parser")
        prodInfo.id = soup.find('input',{'id':'ASIN'})['value']     #  <input type="hidden" id="ASIN" name="ASIN" value="B01BS5A2FS">
        price_etc = soup.find(id='apex_offerDisplay_desktop').get_text()  # $18.00$18.00 ($3.60$3.60 / Fl Oz)  
        price_etc_adjusted = price_etc.replace('$', '(', 1).replace('$', ')', 1) #replace first $ with (, second $ with )
        prodInfo.price=price_etc_adjusted[price_etc_adjusted.find('(')+1 : price_etc_adjusted.find(')')] # extract number between ( and )
        prodInfo.title = soup.find(id='productTitle').get_text().strip()   # Neutrogena Rapid Wrinkle Repair Retinol .....
        rating_etc = soup.find(id='acrPopover').get_text().strip() 
        prodInfo.rating = rating_etc.split(' ')[0]
        
    except TypeError:    
         prodInfo.err_msg = "TypeError (link) in scraping"
    except AttributeError:    
         prodInfo.err_msg = "AttributeError (id) in scraping" 
    except UnboundLocalError:
         prodInfo.err_msg = "UnboundLocalError in scraping?"
    else:
        prodInfo.err_msg = ""
    finally:    
        return prodInfo

## --------------------------------------------------------
## ----- read data from .csv file containing urls 
input_rows = ReadCSVFile(const_file_name_input_urls)

## ----- for each url, scrap data from website, append them to prod_info_list.list
prod_info_list = ProductInfoList()
for input_row in input_rows:
    url = input_row[0]
    product_short_name = input_row[1]
    prod_info = GetProductInfoByAmazonURL(url, product_short_name)
    prod_info_list.append(prod_info)

## ----- save product info list data to .csv   
header_list = ['ProductID', 'ProductShortName', 'Price', 'DateTime', 'Rating', 'Error', 'URL', 'ProductLongName'] #header row 
WriteCSVFile(const_file_name_output_product_info_log, prod_info_list.list, header_list)
