import requests
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO
import datetime
import numpy as np


# Constants: ratios and thresholds
GRmin = 1.05
GBmin = 1.05

Gmin = 60

BIG = 0.1
SMALL = 0.005

STRONG = 1.30
MEDIUM = 1.15



def getCurrentAuroraState(local = False):

    if local != False:
        im = Image.open(local)
        pic_url = local
    else:
        page = requests.get("https://lyckebosommargard.se/auroracam/")

        # parse HTML page
        soup = BeautifulSoup(page.content, 'html.parser')

        # get elements by class name
        imgji = soup.select(".items img")

        # newest picture link
        pic_url = imgji[0].get("src")

        slika = requests.get(pic_url)

        im = Image.open(BytesIO(slika.content))
        #im.show()

    # open 24-02-04_21-13-03_0329.JPG
    #im = Image.open(r"img\24-02-04_21-13-03_0329.JPG")

    # Convert image to numpy array
    img_array = np.array(im)

    out = analyse(img_array)

    # Get datetime from picture name
    date = pic_url.split("/")[-1].split("_")[0]
    time = pic_url.split("/")[-1].split("_")[1]
    # Convert it to datetime object
    currentDateTime = datetime.datetime.strptime(date + " " + time, '%y-%m-%d %H-%M-%S')
    # add 3 min 30 sec
    nextDateTime = currentDateTime + datetime.timedelta(minutes=(3 if currentDateTime.hour < 5 or currentDateTime.hour > 20 else 20), seconds=30)
    # Convert to ISO
    nextDateTimeISO = nextDateTime.isoformat()

    toSleep = max((nextDateTime - datetime.datetime.now()).total_seconds(), 3.3*60)
    out["nextDateTime"] = nextDateTime
    out["nextDateTimeISO"] = nextDateTimeISO
    out["toSleep"] = toSleep
    return(out)

def analyse(img_array):
    # Get image dimensions and crop to top 5/8 of the image
    visina, sirina = img_array.shape[:2]
    img_cropped = img_array[:visina * 5 // 8, :, :]
    
    # Extract RGB channels
    r = img_cropped[:, :, 0].astype(float)
    g = img_cropped[:, :, 1].astype(float)
    b = img_cropped[:, :, 2].astype(float)
    
    # Avoid division by zero
    r_safe = np.where(r == 0, 1, r)
    b_safe = np.where(b == 0, 1, b)
    
    # Calculate ratios
    g_r_ratio = g / r_safe
    g_b_ratio = g / b_safe
    
    # Create mask for aurora pixels
    aurora_mask = (g_r_ratio > GRmin) & (g_b_ratio > GBmin) & (g > Gmin)
    
    # Count aurora pixels and calculate intensities
    auroraPixels = np.sum(aurora_mask).item()
    auroraIntensities = np.sum((g_r_ratio + g_b_ratio) / 2 * aurora_mask).item()
    totalPixels = img_cropped.shape[0] * img_cropped.shape[1]

    ratioAuroraPixels = auroraPixels/totalPixels
    ratioAuroraIntensities = (auroraIntensities/auroraPixels) if ratioAuroraPixels > 0 else 0
    ratioAuroraIntensitiesTotal = auroraIntensities/totalPixels

    print("Aurora pixels", auroraPixels, "Total pixels", totalPixels, "Ratio aurora/total", ratioAuroraPixels, "Ratio aurora intensities", ratioAuroraIntensities, "Ratio aurora intensities total", ratioAuroraIntensitiesTotal)

    out = calculateStrength(ratioAuroraPixels, ratioAuroraIntensities)
    out["auroraPixels"] = auroraPixels
    return(out)

def calculateStrength(ratioAuroraPixels, ratioAuroraIntensities):

    out = {
        "sizeType": "none",
        "strengthType": "none",
        "size": 0,
        "strength": 0
    }

    if(ratioAuroraPixels < SMALL):
        out["sizeType"] = "none"
        print("No aurora")
        #return(out)
    elif(ratioAuroraPixels < 2*SMALL):
        out["sizeType"] = "small"
    else:
        out["sizeType"] = "big"

    out["size"] = round((ratioAuroraPixels/(BIG)*100), 2) # in percent


    if(ratioAuroraIntensities < MEDIUM):
        out["strengthType"] = "weak"
    else:
        out["strengthType"] = "strong"
    
    out["strength"] = round((ratioAuroraIntensities/(STRONG)*100), 2) # in percent

    print(out)
    return(out)

## Write your own logic for running this in a loop
## and for notifications if you are using this
## standalone script.

## To use it within HomeAssistant, see watcher_service.py and README.md (https://github.com/zznidar/aurora-watcher?tab=readme-ov-file#setting-up-on-home-assistant) for installation instructions.