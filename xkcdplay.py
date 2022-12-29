
#! python3
#
# xkcdplay.py - downloads all or limited number of images (comics) from https://xkcd.com/
#
# it's just an example of getting data: parsing, downloading files from web-site
# based on original idea described in book Al Sweigart "Automate the boring stuff with python"
#
# unlike the original, the script downloads only locally missing files
# saved images naming pattern: numPage_fileBaseName.ext
# starts scrapping from basic url .com or from certain page .com/777 you want

import logging
logging.basicConfig(filename = 'log.txt', level = logging.DEBUG, format = '%(asctime)s - %(levelname)s - %(message)s')

import os
import requests
import bs4
import re
from pathlib import Path

# FUNCTIONS

# Returns dictionary with content of local dir with img files
def getRegistry(dirStorage):
    # dictionary: key is numPage, value is nameIMGFile
    dctRegistry = {}
    dirStorage = Path(dirStorage)
    lstFiles = dirStorage.glob('*[0-9]_*.???')

    for pathFile in lstFiles:
        dctRegistry[pathFile.name.split('_')[0]] = pathFile.name

    return dctRegistry

# Returns page number (extracted from url string)
def extractNumPage(pathUrl):
    pat = r'^https?:\/\/.*\/(\d{1,4})\/?$'
    if matched := re.search(pat, pathUrl, re.IGNORECASE):
        return matched.group(1)

# Returns previous page number (extracted from page a href navigation)
def findPrevNumPage(soupObj):
    # Select href like href='/pageNum/'
    prevLink = soupObj.select('a[rel="prev"]')[0]
    # Get number only
    strNum = (prevLink.get('href')).replace('/', '')
    return strNum

# Returns page number (extracted from permanent link) 
def findNumPage(soupObj):
    pat = r'^https?:\/\/.*\/(\d{1,4})\/?$'
    hrefRegex = re.compile(pat, re.IGNORECASE)
    # Return first in list if element matched
    for element in soupObj.find_all(href = hrefRegex):
        return hrefRegex.search(element.get('href')).group(1)

# Returns url string like https://basicUrl/pageNum/
def findImgUrl(soupObj):
    elemImg = soupObj.select('#comic img')
    if elemImg != []:
        return f"https:{elemImg[0].get('src')}"
        

# START

# Starting url
basicUrl = 'https://xkcd.com'

# Folder for savin downloaded images
dirStorage = 'xkcd'
os.makedirs(dirStorage, exist_ok = True) 

# Inventory data in local storage
dctLocalStorage = getRegistry(dirStorage)

# Downloaded files limit
numLimit = 5000
i = 1

# start from basic url or from certain page
pageUrl = basicUrl  # + '/777'
numPage = None

# Iterate over pages on web-site
while not pageUrl.endswith('#') and i <= numLimit:

    if numPage and int(numPage) <= 0:
        break

    # pageUrl format is like basicUrl/numPage/
    if numPage := extractNumPage(pageUrl):
        # Check if current page number already in local storage
        if numPage in dctLocalStorage:
            # Fast way to get previous url
            pageUrl = f'{basicUrl}/{str(int(numPage) - 1)}'
            # Skip current page
            continue

    # Starting request current page
    logging.debug('Request page data %s' % pageUrl)
    res = requests.get(pageUrl)
    try:
        res.raise_for_status()
    except Exception as exc:
        # Can not request a page
        logging.debug('num: {numPage} url: {pageUrl} error occured %s:' % (exc))
        # Fast way to get previous url
        pageUrl = f'{basicUrl}/{str(int(numPage) - 1)}'
        # Skip current page
        continue

    soup = bs4.BeautifulSoup(res.text, 'html.parser')

    # If current page number not extracted from url
    if not numPage:
        # Try find number of page in page structure
        numPage = findNumPage(soup)

    # Check if file number present in local storage
    if numPage in dctLocalStorage:
        # Get previous url from page navigation
        pageUrl = f'{basicUrl}/{findPrevNumPage(soup)}'
        # Skip current page
        continue

    # Find image file url
    if not (imgUrl := findImgUrl(soup)):
        # Nothing to download on current page
        pageUrl = f'{basicUrl}/{str(int(numPage) - 1)}'
        # Skip current page
        continue

    # Download the image
    logging.debug('downloading image %s...' % (imgUrl))
    res = requests.get(imgUrl)
    try:
        res.raise_for_status()
    except Exception as exc:
        logging.debug('num: {numPage} img url: {imgUrl} error occured %s:' % (exc))
    
    # Make file name with rule: numPage_fileBaseName.ext
    pathFile = os.path.join(dirStorage, f'{str(numPage)}_{os.path.basename(imgUrl)}')
    imageFile = open(pathFile,'wb')

    # Save an image to ./dirStorage
    for chunk in res.iter_content(100000):
        imageFile.write(chunk)

    imageFile.close()

    logging.debug(f'done: {i} num: {numPage} img: {imgUrl} page: {pageUrl} file: {pathFile}')
    print(f'done:\t{i}\nnum:\t{numPage}\nimg:\t{imgUrl}\npage:\t{pageUrl}\nfile:\t{pathFile}')

    # Get previous page url
    pageUrl = f'{basicUrl}/{findPrevNumPage(soup)}'
    i += 1

# Show result
logging.debug(f'all ({i - 1}) done!')
print(f'\nall ({i - 1}) done!')