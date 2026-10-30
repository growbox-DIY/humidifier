# main.py - mini ESP (ESP32-C3) in the humidifier: relay controlled by
# the main ESP over ESP-NOW (growbox-firmware, src/humidifier.py).
#
# Safety: the relay is off from boot, switches off after LINK_TIMEOUT_MS
# without a message from the main ESP, and the watchdog resets a hung
# board (off again after the reset).
#
# The main ESP sits on the WiFi router's channel, which can change, so
# after losing the link the mini checks channels 1..13: a unicast "HEL" is
# acknowledged only on the channel the main ESP listens on.
#
# The main ESP's address is not in the code: the mini listens on each
# channel in turn until a "HUM" arrives (sent only by an ESP that has the
# mini as peer in its config), and saves the sender in MAIN_FILE. When the
# saved ESP does not answer for MISSES_BEFORE_SCAN rounds, it searches
# again - replacing the main ESP does not require reflashing the mini.
#
# Flashed over USB:
#   mpremote connect /dev/cu.usbmodem21101 cp src/main.py :main.py
import espnow
import machine
import network
import utime

MAIN_FILE = "main_mac.txt"

RELAY_PIN = 4
# HW-307 (PNP S8550) switches on a low input, and 3.3 V from the ESP does
# not switch it off, so an NPN pulls IN to GND (BC547A: GPIO -> 1k -> base,
# 10k base-GND). GPIO high = relay on; at boot and reset the pin is an
# input and the 10k keeps the transistor off = relay off.
RELAY_ACTIVE_LOW = False

# the main ESP sends the state every 5 s
LINK_TIMEOUT_MS = 20000
WDT_TIMEOUT_MS = 10000
CHANNELS = range(1, 14)
# the main ESP sends HUM every 5 s - listen this long on each channel
LISTEN_MS = 6000
MISSES_BEFORE_SCAN = 3

_OFF = 1 if RELAY_ACTIVE_LOW else 0
_relay = machine.Pin(RELAY_PIN, machine.Pin.OUT, value=_OFF)
# on-board LED (GPIO 8, active low): lit = link up
_led = machine.Pin(8, machine.Pin.OUT, value=1)

_state = 0


def set_relay(on):
    global _state

    on = 1 if on else 0

    if on != _state:
        print("RELAY:", "ON" if on else "OFF")

    _state = on
    _relay.value(on ^ RELAY_ACTIVE_LOW)


def load_main():
    try:
        with open(MAIN_FILE) as f:
            return bytes.fromhex(f.read().strip())
    except (OSError, ValueError):
        return None


def save_main(mac):
    with open(MAIN_FILE, "w") as f:
        f.write(mac.hex())


def add_peer(e, mac):
    try:
        e.add_peer(mac)
    except OSError:
        pass  # already added (ESP_ERR_ESPNOW_EXIST)


def find_channel(sta, e, wdt, main_mac):
    """Main ESP channel, or None after a full round."""
    for ch in CHANNELS:
        wdt.feed()
        sta.config(channel=ch)

        try:
            if e.send(main_mac, b"HEL"):
                print("LINK: main ESP on channel", ch)
                return ch
        except OSError:
            pass

    return None


def discover(sta, e, wdt):
    """Address of the ESP sending us HUM, or None after a full round."""
    print("LINK: searching for main ESP")

    for ch in CHANNELS:
        sta.config(channel=ch)
        deadline = utime.ticks_add(utime.ticks_ms(), LISTEN_MS)

        while utime.ticks_diff(deadline, utime.ticks_ms()) > 0:
            wdt.feed()
            mac, msg = e.recv(500)

            if msg and msg[:3] == b"HUM" and len(msg) == 4:
                print("LINK: found main ESP", mac.hex(":"), "on channel", ch)
                return bytes(mac)

    return None


def main():
    wdt = machine.WDT(timeout=WDT_TIMEOUT_MS)

    sta = network.WLAN(network.STA_IF)
    sta.active(True)
    sta.disconnect()

    e = espnow.ESPNow()
    e.active(True)

    main_mac = load_main()

    if main_mac:
        add_peer(e, main_mac)

    print("Humidifier node", sta.config("mac").hex(":"),
          "main", main_mac.hex(":") if main_mac else "unknown")

    last_msg = None
    misses = 0

    while True:
        wdt.feed()

        linked = (
            last_msg is not None
            and utime.ticks_diff(utime.ticks_ms(), last_msg) < LINK_TIMEOUT_MS
        )

        if not linked:
            if last_msg is not None:
                print("LINK: lost -> relay OFF")
                last_msg = None

            set_relay(0)
            _led.value(1)

            if main_mac and find_channel(sta, e, wdt, main_mac):
                misses = 0
            elif main_mac and misses < MISSES_BEFORE_SCAN:
                misses += 1
                utime.sleep_ms(1000)
                continue
            else:
                found = discover(sta, e, wdt)

                if found is None:
                    continue

                if found != main_mac:
                    add_peer(e, found)
                    save_main(found)
                    main_mac = found

                misses = 0

            # channel found - wait for HUM (the main ESP answers HEL)
            last_msg = utime.ticks_ms()

        mac, msg = e.recv(1000)

        if mac != main_mac or not msg:
            continue

        if msg[:3] == b"HUM" and len(msg) == 4:
            last_msg = utime.ticks_ms()
            _led.value(0)
            set_relay(msg[3])

            try:
                e.send(main_mac, b"HST" + bytes([_state]), False)
            except OSError as err:
                print("LINK: reply error:", err)


try:
    main()
finally:
    # exception or Ctrl-C: the humidifier must not be left on unsupervised
    set_relay(0)
