# OREI HDMI Matrix Integration for Home Assistant

A custom [Home Assistant](https://www.home-assistant.io/) integration for the **OREI UHD44-EXB400R-K HDBaseT 4x4 HDMI Extender Matrix**.

This integration is not intended to replace the matrix's built-in web management interface. Rather, it brings the main control and automation capabilities of the matrix into Home Assistant — letting you route inputs to outputs, monitor signal status, and build automations around your AV setup.

## Features

- **Input routing** — Select which HDMI input feeds each output via simple dropdown entities
- **Power control** — Turn the matrix on/off with a switch entity
- **Signal detection** — Binary sensors show which inputs have an active signal and which outputs are connected
- **Custom Lovelace card** — Visual matrix grid and list views for quick routing changes
- **Auto-discovery** — Input and output names are pulled from the device automatically
- **Local polling** — Communicates directly with the device over your LAN (no cloud)

## Supported Hardware

- **OREI UHD44-EXB400R-K** HDBaseT 4x4 HDMI Extender Matrix
- Other OREI matrix models using the same HTTP/JSON API at `/cgi-bin/instr` may also work

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Click the three-dot menu in the top right and select **Custom repositories**
3. Add this repository URL and select **Integration** as the category
4. Click **Download** on the OREI HDMI Matrix integration
5. Restart Home Assistant

### Manual

1. Copy the `custom_components/orei_matrix/` folder into your Home Assistant `config/custom_components/` directory
2. Restart Home Assistant

### Lovelace Card

The custom card is bundled with the integration. It is served and registered as a Lovelace resource automatically — no manual steps needed. Just add it to your dashboard:

```yaml
type: custom:orei-matrix-card
```

## Setup

1. Go to **Settings > Devices & Services > Add Integration**
2. Search for **OREI HDMI Matrix**
3. Enter the IP address of your matrix switcher
4. The integration will connect to the device and create entities automatically

## Entities

| Entity Type | Count | Description |
|-------------|-------|-------------|
| Select | 4 | One per output — dropdown to choose which input is routed |
| Switch | 1 | Matrix power on/off |
| Binary Sensor | 8 | 4 input signal sensors + 4 output connection sensors |

Entity names default to the names configured on the device. You can rename them in Home Assistant via **Settings > Devices & Services > OREI HDMI Matrix** — these renames are local to Home Assistant and will appear in the dashboard card and automations.

## Lovelace Card

The custom card provides two views, toggled by a button in the header:

- **Grid view** — Inputs as columns, outputs as rows. Click a cell to route that input to the output. Active routes are highlighted.
- **List view** — Each output shown with a dropdown to select its input. Compact and mobile-friendly.

Both views show signal status indicators and a power toggle.

## Automation Examples

Route input 1 to output 3 when a scene is activated:

```yaml
service: select.select_option
target:
  entity_id: select.orei_matrix_output_3
data:
  option: "Input 1"
```

Turn off the matrix at midnight:

```yaml
service: switch.turn_off
target:
  entity_id: switch.orei_matrix_power
```

## License

[MIT](LICENSE)
