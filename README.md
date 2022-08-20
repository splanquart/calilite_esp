# Caliblite_esp

Caliblite is a simple application to control calibration light from ESP32 and surely other microcontroler.

It's based on micropython framework.
I wrote this for my own spectroscopy needs around the Star'Ex and Uvex projects.

## Basic
Caliblite provide a simple HTTP API to: 
- get state of lights: `GET /lights`
- change state of a light : `POST /light/<id-of-light>/on` or `POST /light/<id-of-light>/off`

for example:

```
curl http://<esp_ip>/lights

[{"state": 0, "light": 0}, {"state": 0, "light": 0}]
```

To switch on the first light call:

```
curl -X POST http://<esp_ip>/light/0/on

```
