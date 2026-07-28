# ZTE Router MAC Whitelist Manager

A browser automation tool that manages the Wi-Fi MAC address whitelist on a ZTE router through its web UI — no SSH, no API, just Playwright driving the router's browser interface directly.

---

## What it does

- Launches a Chromium browser and logs into the router's web interface using credentials stored in a `.env` file.
- Navigates to the Wi-Fi MAC filter settings page.
- Reads the live whitelist table from the router and cross-references it against a local JSON database of known hostnames and their MAC addresses (`mac_address.json`).
- Displays a rich terminal table showing all known hosts and whether each one is currently whitelisted.
- Prompts the user to select an action and choose a hostname via an interactive CLI menu.
- Performs one of two actions:
  - **Add / Sync** — If the MAC is already in the whitelist, it deletes and re-adds it (sync). If it's not present, it simply adds it.
  - **Remove** — Deletes the MAC from the whitelist if it exists; skips gracefully if it doesn't.
- Automatically enables the MAC whitelist feature on the router if it's currently turned off (add-only flow).
- Takes a full-page screenshot (`example.png`) on exit.

---

## Project Structure

```
zte_router_automation/
├── main.py             # Main automation script
├── mac_address.json    # Hostname → MAC address database
├── .env                # Router credentials (not committed to git)
└── example.png         # Screenshot captured on last run
```

---

## Setup

### 1. Activate the virtual environment

```cmd
py_venv\Scripts\activate.bat
```

Or in PowerShell:

```powershell
py_venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```cmd
pip install -r requirements.txt
```

### 3. Install Playwright browsers (first time only)

```cmd
playwright install
```

### 4. Configure environment variables

Create `zte_router_automation/.env`:

```env
PASSWORD=your_router_password
ROUTER_URL=http://192.168.0.1/index.html#login
```

| Variable     | Description                       |
| ------------ | --------------------------------- |
| `PASSWORD`   | Router web UI login password      |
| `ROUTER_URL` | Full URL to the router login page |

---

## Running

```cmd
cd zte_router_automation
python main.py
```

The browser will open visually by default. Follow the interactive prompts in the terminal to add or remove a device from the whitelist.

To run without a visible browser window, change this line in `main.py`:

```python
browser = p.chromium.launch(headless=True)
```

---

## MAC Address Database

`mac_address.json` maps hostnames to MAC addresses. Add or remove entries here to control which devices appear in the CLI menu.

```json
{
  "HOSTNAME-001": "AA:BB:CC:DD:EE:FF",
  "HOSTNAME-002": "11:22:33:44:55:66"
}
```

---

## Key Libraries

| Library         | Purpose                                     |
| --------------- | ------------------------------------------- |
| `playwright`    | Browser automation for the router web UI    |
| `rich`          | Terminal tables, panels, and styled logging |
| `InquirerPy`    | Interactive CLI prompts and selection menus |
| `pyfiglet`      | ASCII art banner displayed on startup       |
| `python-dotenv` | Loading router credentials from `.env`      |

---

## Notes

- The `.env` file contains sensitive credentials — keep it out of version control (already covered by `.gitignore`).
- The router must be reachable on the network at the IP defined in `ROUTER_URL` when running the script.
- You can create`mac_address.json` to hold your pc's hostname and mac addresses.
