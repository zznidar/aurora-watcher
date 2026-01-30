# aurora-watcher
Watches livecam photos and notifies when aurora is visible


## Setting up on Home Assistant
### Installing plugins
I recommend 2 plugins for this to work:
* [VSCode](https://github.com/hassio-addons/addon-vscode). This will allow you to easily upload and modify files we need for setting up Aurora Watcher.
    1. Settings -> Add-ons -> Add-on store -> search for "VScode" -> follow installation steps (probably just clicking "Next" or "Install")
* [pyscript](https://github.com/custom-components/pyscript). This is required for the Aurora Watcher to run.
    1. Settings -> Devices & services -> HACS -> somehow add "pyscript". 
    2. Follow their documentation for more info.
    3. Settings -> Devices & services -> Add integration -> `Pyscript Python scripting`
        * I am not sure whether you should tick or untick the boxes. I allowed imports and accessing hass.
        * NOTE: If it fails ("Integration is already installed") but you don't see it anywhere, go to home assistant Settings -> 
Devices & services -> in the top-right corner area, Show 5 disabled integrations (or maybe click the Filtering icon -> Show disabled/ignored integrations)
* [Apprise](https://www.home-assistant.io/integrations/apprise/). This is needed to send you notifications when aurora is detected.
    1. Not sure, consult thier documentation. Maybe it is already preinstalled – in that case, you just need to add a few lines to the configuration.yaml file.


### Setting up Aurora Detector
1. Open `Studio Code Server` inside your HomeAssistant
    * If you don't see any of the aftermentioned files, go to Hamburger Menu -> File -> Open **Folder**... -> `~/config`
2. Add the file `watcher_service.py` and rename it to `watcher.py` into the `/root/config/pyscript` folder
3. Restart Home Assistant (Developer tools -> Check configuration, then (if everything is ok) -> Restart). Make sure the Python script starts running and that it runs at least once successfully.
    * This will create new sensors for you, particularly the `sensor.zzaurorastrength`
    * You can find logs in Settings -> System -> Logs -> three dots -> Show all logs
        * You should see something like 
            ```log
            2026-01-30 19:34:35.861 INFO (MainThread) [custom_components.pyscript.file.watcher.getCurrentAuroraState] 2024-02-06T20:11:58
            2026-01-30 19:34:37.159 INFO (MainThread) [custom_components.pyscript.file.watcher.getCurrentAuroraState] b'<!DOCTYPE html>\r\n<html lang="e'
            2026-01-30 19:34:37.166 INFO (MainThread) [custom_components.pyscript.file.watcher.getCurrentAuroraState] New picture: https://[...]/wp-content/uploads/Webcam//26-01-30_19-32-29_9999.JPG is not the same as https://[...]/wp-content/uploads/Webcam//26-01-30_14-40-42_9999.JPG
            ```
        * Around a minute later, you should get a result:
            ```log
            2026-01-30 19:35:55.597 INFO (MainThread) [custom_components.pyscript.file.watcher.getCurrentAuroraState] {'sizeType': 'none', 'strengthType': 'none', 'size': 0, 'strength': 0, 'auroraPixels': 19, 'nextDateTimeISO': '2026-01-30T19:52:59'}
            ```
4. Set up notifications via Apprise

### Setting up notifications via Apprise
Notifications can be set up as Apprise, for example:  
1. Studio Code Server -> `/root/config/configuration.yaml`:
    ```yaml
    notify:
    - name: ZZ_Aurora_notifier
        platform: apprise
        url: mailto://senderMailUsername:password@gmail.com?to="recipientEmail%2BAurora80@gmail.com,yourFriend@email.something"
    ```
2. Reload (Developer tools -> All YAML configuration)
3. Setttings -> Automations & Scenes -> Create automation -> When `sensor.zzaurorastrength` is above 80, Then do Notifications (e. g. send a push notification to your phone, send an e-mail ...). If you also want a link to the latest livecam picture, use this as the message:
    ```yaml
    Aurora intensity is over 80 %   <br>  
    Current view: <a href="{{ states('sensor.zzauroralastpicurl') }}">{{ states('sensor.zzauroralastpicurl') }}</a>
    ```
    * To also be notified when the northern lights start building up, create another automation with the Trigger `sensor.zzaurorastrengthtype` changes to `weak`. This will allow you to catch the aurora if it is more short-lived.



The script should run every 4 minutes. According to current time and aurora possibility (higher during night), it will get the newest picture from the livecam and analyse it. Values will be written into various sensors (aurora strength, last check time ...). Note: the sensors are unavailable and invisible when the script is not running successfully.

Note: the livecam used by Aurora Watcher may become unavailable at any time. I am thankful for its operation while it worked, it allowed me to immerse into a beautiful aurora dance.  
As of 2026, the livecam became available again; the watcher script has been modified to point to the new source.