## New version as of 2026-02-18
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
import auroraanalyse


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

    out = await auroraanalyse.analyse(img_array)

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


if __name__ == "__main__":
    print(getCurrentAuroraState())
