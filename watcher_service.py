## New version as of 2026-02-15
## Make sure you create sensors in template.yaml
## and restart all YAML config
## before you create this file!!!

import requests
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO
import json
#from pyscript import haas
import pyscript
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


unitsOfMeasurement = {
    "size3": "%",
    "strength3": "%",
    "auroraPixels3": "px"
}
icon_yes = "mdi:aurora"
icon_no = "mdi:string-lights-off"


@time_trigger("period(now, 4min)")
def getCurrentAuroraState():
    ## First check if enough time has passed since previous run (at least 4 minutes)
    try:
        nextDateTimeIso = state.get("sensor.zzauroranextdatetimeiso3")
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
        lastPicUrl = state.get("sensor.zzauroralastpicurl3")
    except:
        lastPicUrl = "https://lyckebosommargard.se/wp-content/uploads/Webcam//26-01-30_14-40-42_9999.JPG"
    if(lastPicUrl == pic_url):
        log.info("Same picture as last time, skipping")
        return
    
    log.info(f"New picture: {pic_url} is not the same as {lastPicUrl}")
    

    async_result2 = await hass.async_add_executor_job(requests.get, pic_url) # tuple of args for foo
    slika = async_result2.content

    im = Image.open(BytesIO(slika))

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
    out["nextDateTimeISO3"] = nextDateTimeISO
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
        attributes["unique_id"] = f"sensor.zzaurora{key.lower()}"
        state.set(f"sensor.zzaurora{key.lower()}", value, attributes)

    state.set("sensor.zzauroralastpicurl3", pic_url, {"unique_id": "sensor.zzauroralastpicurl3"})
    return(json.dumps(out))

def analyse(img_array):
    # Get image dimensions and crop to top 5/8 of the image
    visina, sirina = img_array.shape[:2]
    #img_cropped = img_array[:visina * 5 // 8, :, :]
    img_cropped = img_array[:visina * 5 // 8]

    # Transpose img_cropped in such a way that the r value becomes the first axis
    img_cropped = np.transpose(img_cropped, (2, 0, 1))
    
    # Extract RGB channels
    r = img_cropped[0].astype(float)
    g = img_cropped[1].astype(float)
    b = img_cropped[2].astype(float)
    
    # Avoid division by zero
    r_safe = np.where(np.equal(r, 0), 1, r)
    b_safe = np.where(np.equal(b, 0), 1, b)
    
    # Calculate ratios
    g_r_ratio = g / r_safe
    g_b_ratio = g / b_safe
    
    # Create mask for aurora pixels
    aurora_mask = np.logical_and(np.greater(g_r_ratio, GRmin), np.logical_and(np.greater(g_b_ratio, GBmin), np.greater(g, Gmin)))
    
    # Count aurora pixels and calculate intensities
    auroraPixels = np.sum(aurora_mask).item()
    auroraIntensities = np.sum((g_r_ratio + g_b_ratio) / 2 * aurora_mask).item()
    totalPixels = img_cropped.shape[1] * img_cropped.shape[2] # because it is now transposed

    ratioAuroraPixels = auroraPixels/totalPixels
    ratioAuroraIntensities = (auroraIntensities/auroraPixels) if auroraPixels > 0 else 0
    ratioAuroraIntensitiesTotal = auroraIntensities/totalPixels

    print("Aurora pixels", auroraPixels, "Total pixels", totalPixels, "Ratio aurora/total", ratioAuroraPixels, "Ratio aurora intensities", ratioAuroraIntensities, "Ratio aurora intensities total", ratioAuroraIntensitiesTotal)

    out = calculateStrength(ratioAuroraPixels, ratioAuroraIntensities)
    out["auroraPixels3"] = auroraPixels
    return(out)

def calculateStrength(ratioAuroraPixels, ratioAuroraIntensities):

    out = {
        "sizeType3": "none",
        "strengthType3": "none",
        "size3": 0,
        "strength3": 0
    }

    if(ratioAuroraPixels < SMALL):
        out["sizeType3"] = "none"
        print("No aurora")
        return(out)
    elif(ratioAuroraPixels < 2*SMALL):
        out["sizeType3"] = "small"
    else:
        out["sizeType3"] = "big"

    out["size3"] = round((ratioAuroraPixels/(BIG)*100), 2) # in percent


    if(ratioAuroraIntensities < MEDIUM):
        out["strengthType3"] = "weak"
    else:
        out["strengthType3"] = "strong"
    
    out["strength3"] = round((ratioAuroraIntensities/(STRONG)*100), 2) # in percent

    print(out)
    return(out)

if __name__ == "__main__":
    print(getCurrentAuroraState())
