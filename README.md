# aurora-watcher
Watches livecam photos and notifies when aurora is visible


## Setting up on Home Assistant
0. Settings -> Integrations -> Add "Pyscript Python scripting" integration (you probably have to install this customly)
1. Add the file `watcher_service.py` as `watcher.py` into the `pyscript` folder
2. Make sure the Python script starts running and that it runs at least once successfully.
    * This will create new sensors for you, particularly the `sensor.zzaurorastrength`
3. Setttings -> Automations & Scenes -> Create automation -> When `sensor.zzaurorastrength` is above 80, Then do Notifications (e. g. send a push notification to your phone, send an e-mail ...)
    * To also be notified when the northern lights start building up, use the Trigger `sensor.zzaurorastrengthtype` changes to`weak`. This will allow you to catch the aurora if it is more short-lived.

Notifications can be set up as Apprise, for example:  
Studio Code Server -> `configuration.yaml`:
```yaml
notify:
  - name: ZZ_Aurora_notifier
    platform: apprise
    url: mailto://senderMailUsername:password@gmail.com?to="recipientEmail%2BAurora80@gmail.com,yourFriend@email.something"
```


The script should run every 4 minutes. According to current time and aurora possibility (higher during night), it will get the newest picture from the livecam and analyse it. Values will be written into various sensors (aurora strength, last check time ...). Note: the sensors are unavailable and invisible when the script is not running successfully.

Note: the livecam used by Aurora Watcher is not available anymore. I am thankful for its operation while it worked, it allowed me to immerse into a beautiful aurora dance.