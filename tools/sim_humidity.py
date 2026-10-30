# sim_humidity.py - humidifier test without a sensor, on a dev (main) ESP
#
# Real logic from growbox-firmware (App/humidifier.py), only
# sensor.get() returns a fake humidity: a drop below the "min" threshold
# and a rise back above "max". The script
# goes to RAM only and uses the modules already flashed on the board:
#   mpremote connect /dev/cu.usbserial-0001 run tools/sim_humidity.py
# Opening the port resets the ESP, and Ctrl-C does not work while the
# firmware boots - if mpremote reports "could not enter raw repl", wait
# for the boot to finish and connect without a reset. The interrupted
# firmware leaves its tasks in the asyncio loop (the scheduler also calls
# humidifier.update).
#
# When done, the watchdog from the interrupted program resets the board,
# so the normal firmware comes back.
import machine
import uasyncio as asyncio
import utime

import humidifier
import sensor

# humidity in %, one step every STEP_S
PROFILE = (55, 52, 50, 48, 46, 44, 42, 40, 40, 42, 44, 46, 48, 50, 52, 55)
STEP_S = 5

CONFIG = {
    "auto": {"enabled": False},
    "humidifier": {
        "peer": "10003baf0ae8",
        "manual": {"enabled": True, "min": 45, "max": 50},
        "auto": {"enabled": False, "min": 45, "max": 50},
        "fan": {"maxLevel": 40, "tempLimit": 27},
    },
}

# switch lockout cut from 60 s so the test takes ~1.5 min
humidifier.MIN_SWITCH_S = 5

_humidity = PROFILE[0]


def _fake_get():
    return {"temperature": 24.0, "humidity": _humidity, "ts": utime.time()}


sensor.get = _fake_get


def _report(label):
    st = humidifier.status()
    print("SIM: %s hum=%d%% want=%s mini=%s online=%s" % (
        label, _humidity, "ON" if st["want"] else "OFF",
        "ON" if st["on"] else "OFF", st["online"]))


async def sim():
    global _humidity

    # the watchdog from the interrupted program keeps counting - feed it
    wdt = machine.WDT(timeout=60000)
    asyncio.create_task(humidifier.link_task(CONFIG))

    for _ in range(10):
        wdt.feed()
        await asyncio.sleep(1)

    _report("start")

    for h in PROFILE:
        _humidity = h

        for _ in range(STEP_S):
            wdt.feed()
            humidifier.update(CONFIG, True)
            await asyncio.sleep(1)

        _report("step")

    # end: humidifier off regardless of humidity
    CONFIG["humidifier"]["manual"]["enabled"] = False
    humidifier.update(CONFIG, True)

    for _ in range(8):
        wdt.feed()
        await asyncio.sleep(1)

    _report("end")


asyncio.run(sim())
