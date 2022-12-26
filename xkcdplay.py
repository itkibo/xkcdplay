
#! python3
# xkcdplay.py - downloads all or limit number of images (comics) from https://xkcd.com/ 
# it's just an example of getting data: parsing, downloading files from web-site
# based on original idea described in book Al Sweigart "Automate the boring stuff with python"
# unlike the original, the script downloads only locally missing files

import logging
logging.basicConfig(filename = 'log.txt', level = logging.DEBUG, format = '%(asctime)s - %(levelname)s - %(message)s')

import os, requests, bs4, re
from pathlib import Path

# FUNCTIONS

# returns dictionary = content of storage dir with files
# key = file number, value = file name
def getRegistry(dirStorage):
    dctRegistry = {}
    dirStorage = Path(dirStorage)
    lstFiles = dirStorage.glob('????_*.???')
    for pathFile in lstFiles:
        dctRegistry[pathFile.name.split('_')[0]] = pathFile.name

    return dctRegistry

# returns page number (from url string)
def extractNumPage(pathUrl):
    pat = r'^https?:\/\/.*\/(\d{1,4})\/?$'
    if matched := re.search(pat, pathUrl, re.IGNORECASE):
        return matched.group(1)

# returns previous page number (from page navigation)
def findPrevNumPage(soupObj):
    # select href and extract previous number of page
    prevLink = soupObj.select('a[rel="prev"]')[0]
    # example: href='/2142/'
    strNum = (prevLink.get('href')).replace('/', '')
    return strNum

# returns page number (from permanent link) 
def findNumPage(soupObj):
    pat = r'^https?:\/\/.*\/(\d{1,4})\/?$'
    hrefRegex = re.compile(pat, re.IGNORECASE)
    # return first in list if element matched
    for element in soupObj.find_all(href = hrefRegex):
        return hrefRegex.search(element.get('href')).group(1)

# returns url string like https://website.com/pageNum/
def findImgUrl(soupObj):
    elemImg = soupObj.select('#comic img')
    if elemImg != []:
        return f"https:{elemImg[0].get('src')}"
        

# START

# starting url
basicUrl = 'https://xkcd.com'
# folder for savin downloaded images
dirStorage = 'xkcd'
os.makedirs(dirStorage, exist_ok = True) 

# inventory data in local storage
dctLocalStorage = getRegistry(dirStorage)

# downloaded files limit
limit = 5000
i = 1

pageUrl = basicUrl
while not pageUrl.endswith('#') and i <= limit:

    # pageUrl format is like basicUrl/numPage/
    if numPage := extractNumPage(pageUrl):
        # check if current page number already in local storage
        if numPage in dctLocalStorage:
            # fast way to generate previous url
            pageUrl = f'{basicUrl}/{str(int(numPage) - 1)}'
            # skip current page
            continue

    # starting request
    logging.debug('Request page data %s' % pageUrl)
    res = requests.get(pageUrl)
    res.raise_for_status()
    soup = bs4.BeautifulSoup(res.text, 'html.parser')

    # if current page number not extracted from url
    if not numPage:
        # try find numper of page in page structure
        numPage = findNumPage(soup)

    # check if detected number present locally
    if numPage in dctLocalStorage:
        # generate previous url from page navigation
        pageUrl = f'{basicUrl}/{findPrevNumPage(soup)}'
        # skip current page
        continue

    # find image file url
    if not (imgUrl := findImgUrl(soup)):
        # nothing to download on current page
        pageUrl = f'{basicUrl}/{str(int(numPage) - 1)}'
        # skip current page
        continue

    # download the image
    logging.debug('downloading image %s...' % (imgUrl))
    res = requests.get(imgUrl)
    try:
        res.raise_for_status()
    except Exception as exc:
        logging.debug('num: {numPage} img url: {imgUrl} error occured %s:' % (exc))
    
    # save the image to ./dirStorage
    pathFile = os.path.join(dirStorage, f'{str(numPage)}_{os.path.basename(imgUrl)}')
    imageFile = open(pathFile,'wb')
    for chunk in res.iter_content(100000):
        imageFile.write(chunk)

    imageFile.close()

    logging.debug(f'done: {i} num: {numPage} img: {imgUrl} page: {pageUrl} file: {pathFile}')
    print(f'done:\t{i}\nnum:\t{numPage}\nimg:\t{imgUrl}\npage:\t{pageUrl}\nfile:\t{pathFile}')

    # previous page url
    pageUrl = f'{basicUrl}/{findPrevNumPage(soup)}'
    i += 1

logging.debug(f'all ({i - 1}) done!')
print(f'\nall ({i - 1}) done!')