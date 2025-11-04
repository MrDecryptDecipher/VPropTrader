# Install Python on Windows - Step by Step

## Step 1: Download Python

1. Open your web browser
2. Go to: **https://www.python.org/downloads/**
3. Click the big yellow button: **"Download Python 3.12.x"**
4. Save the file (it will be named something like `python-3.12.0-amd64.exe`)

## Step 2: Install Python

1. **Find the downloaded file** (usually in your Downloads folder)
2. **Double-click** the installer file
3. **IMPORTANT:** ✅ Check the box that says **"Add Python to PATH"** (at the bottom)
4. Click **"Install Now"**
5. Wait for installation to complete (1-2 minutes)
6. Click **"Close"**

## Step 3: Verify Installation

1. Open a **NEW** PowerShell window (close the old one)
2. Type this command:
   ```powershell
   python --version
   ```
3. You should see: `Python 3.12.x`

## Step 4: Install Required Packages

In PowerShell, run:
```powershell
python -m pip install MetaTrader5 requests
```

You should see:
```
Successfully installed MetaTrader5-5.0.x requests-2.31.x
```

## Step 5: Download the Trading Script

1. Copy the `windows_auto_trader.py` file to your Windows machine
2. Save it somewhere easy to find, like:
   - `C:\Trading\windows_auto_trader.py`
   - Or your Desktop

## Step 6: Run the Auto Trader

### Method 1: Double-Click
1. Find `windows_auto_trader.py`
2. Right-click → **Open with** → **Python**

### Method 2: PowerShell
```powershell
cd C:\Trading
python windows_auto_trader.py
```

## Troubleshooting

### "python is not recognized"

**Problem:** Python not added to PATH

**Solution:**
1. Uninstall Python (Control Panel → Programs)
2. Reinstall and make SURE to check "Add Python to PATH"
3. Restart PowerShell

### "pip is not recognized"

**Solution:** Use `python -m pip` instead of just `pip`:
```powershell
python -m pip install MetaTrader5 requests
```

### Can't find the installer

Download directly: https://www.python.org/ftp/python/3.12.0/python-3.12.0-amd64.exe

## Quick Test

After installation, test everything works:

```powershell
python -c "import MetaTrader5; print('MT5 package installed!')"
```

Should print: `MT5 package installed!`

## Next Steps

Once Python is installed:
1. Make sure MT5 is running and logged in
2. Run `python windows_auto_trader.py`
3. Watch it automatically trade!

---

**Total time: 5 minutes**
