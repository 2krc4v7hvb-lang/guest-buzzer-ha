# Guest Access Buzzer — Home Assistant integration

A UI-configurable Home Assistant integration for the room1619 / guest-access
buzzer system. Adds a device with:

- **Binary sensor** — *Armed* (on while the buzzer's arm window is active), with
  `seconds_remaining`, `window_seconds`, and `buzzer_enabled` attributes.
- **Button** — *Arm buzzer* (arms a window via the cloud endpoint).

No YAML editing — set it up entirely from **Settings → Devices & Services**.

## Install via HACS

1. In Home Assistant, open **HACS → Integrations**.
2. Top-right **⋮ → Custom repositories**.
3. Add this repository's URL, category **Integration**, then **Add**.
4. Find **Guest Access Buzzer** in the list, **Download**, and **restart** Home Assistant.

## Set up

1. **Settings → Devices & Services → Add Integration**.
2. Search **Guest Access Buzzer**.
3. Enter:
   - **Base URL** — e.g. `https://room1619.com`
   - **Arm key** — from the admin under **Buzzer Settings → Siri / Shortcuts**
     (the value after `?key=` in the Arm URL).

That's it — the device and its entities are created automatically.

## Options

The integration's **Configure** button (on its card in Devices & Services) lets
you set the **poll interval** (5–300 seconds, default 15). Changes apply
immediately.

## Notes

- The base URL + key together identify one property, so you can add multiple
  properties as separate entries.
