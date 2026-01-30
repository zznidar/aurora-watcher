import requests
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO
import datetime


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

    # get pixel data
    pix = im.load()
    sirina, visina = im.size # Get the width and hight of the image for iterating over

    out = analyse(pix, sirina, visina)

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

def analyse(pix, sirina, visina):
    totalPixels = 0
    auroraPixels = 0
    auroraIntensities = 0

    for x in range(sirina):
        for y in range(visina * 5 // 8):
            r, g, b = pix[x, y]
            if(GRmin < g/(r or 1) and GBmin < g/(b or 1) and g > Gmin):
                # Aurora pixel
                auroraPixels += 1
                auroraIntensities += (g/(r or 1) + g/(b or 1))/2
            totalPixels += 1
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