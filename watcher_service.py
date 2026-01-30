import requests
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO
import json
#from pyscript import haas
import pyscript
import datetime


# Constants: ratios and thresholds
GRmin = 1.05
GBmin = 1.05

Gmin = 60

BIG = 0.1
SMALL = 0.005

STRONG = 1.30
MEDIUM = 1.15


unitsOfMeasurement = {
    "size": "%",
    "strength": "%",
    "auroraPixels": "px"
}
icon_yes = "mdi:aurora"
icon_no = "mdi:string-lights-off"


@time_trigger("period(now, 4min)")
def getCurrentAuroraState():
    ## First check if enough time has passed since previous run (at least 4 minutes)
    try:
        nextDateTimeIso = state.get("sensor.zzauroranextdatetimeiso")
    except:
        nextDateTimeIso = "2024-02-06T20:11:58"
    log.info(nextDateTimeIso)

    nextDateTime = datetime.datetime.fromisoformat(nextDateTimeIso)

    if(datetime.datetime.now() < nextDateTime):
        # We still need to sleep! See you on next time trigger!
        log.info("We still need to sleep! See you on next time trigger!")
        return


    async_result = await hass.async_add_executor_job(requests.get, "https://lyckebosommargard.se/auroracam/") # tuple of args for foo

    # do some other stuff in the main process

    page = async_result.content  # get the return value from your function.
    log.info(page[:30])

    # parse HTML page
    soup = BeautifulSoup(page, 'html.parser')

    imgji = soup.select(".items img")
    
    pic_url = imgji[0].get("src")

    # Check that the picture is not the same as the previous one
    try:
        lastPicUrl = state.get("sensor.zzauroralastpicurl")
    except:
        lastPicUrl = "https://lyckebosommargard.se/wp-content/uploads/Webcam//26-01-30_14-40-42_9999.JPG"
    if(lastPicUrl == pic_url):
        log.info("Same picture as last time, skipping")
        return
    
    log.info(f"New picture: {pic_url} is not the same as {lastPicUrl}")
    

    async_result2 = await hass.async_add_executor_job(requests.get, pic_url) # tuple of args for foo
    slika = async_result2.content

    im = Image.open(BytesIO(slika))

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
    out["nextDateTimeISO"] = nextDateTimeISO
    #out["toSleep"] = toSleep

    log.info(out)

    # For each key, value in out, set the state and attributes
    for key, value in out.items():
        attributes = {}
        attributes["icon"] = icon_no

        if key in unitsOfMeasurement:
            attributes["unit_of_measurement"] = unitsOfMeasurement[key]
        if value in ["big", "strong"] or (not isinstance(value, str) and value > 60):
            attributes["icon"] = icon_yes
        state.set(f"sensor.zzaurora{key.lower()}", value, attributes)

    state.set("sensor.zzauroralastpicurl", pic_url)
    return(json.dumps(out))

import asyncio
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
        asyncio.sleep(0)

    ratioAuroraPixels = auroraPixels/totalPixels
    ratioAuroraIntensities = (auroraIntensities/auroraPixels) if auroraPixels > 0 else 0
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
        return(out)
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

if __name__ == "__main__":
    print(getCurrentAuroraState())
