# ✅ Copy Corrected MT5 EA Files to Windows

The EA files on your Ubuntu server are already corrected and ready to use!

## 📋 Quick Fix

You need to **re-copy** the files from Ubuntu to Windows because the Windows version got corrupted during compilation attempts.

### Files to Copy (from Ubuntu to Windows):

```
FROM Ubuntu: ~/Sandeep/projects/Vproptrader/mt5_ea/
TO Windows: C:\Users\Superagent\AppData\Roaming\MetaQuotes\Terminal\2A7A61598246A894915935526B662613\MQL5\Experts\
```

### Exact Files:

1. **QuantSupraAI.mq5** → Copy to `Experts\` folder
2. **config.mqh** → Copy to `Experts\` folder  
3. **Include/RestClient.mqh** → Copy to `Experts\Include\`
4. **Include/RiskManager.mqh** → Copy to `Experts\Include\`
5. **Include/TradeEngine.mqh** → Copy to `Experts\Include\`
6. **Include/Governors.mqh** → Copy to `Experts\Include\`

---

## 🚀 Method 1: Download ZIP from Ubuntu

**On Ubuntu terminal:**

```bash
cd ~/Sandeep/projects/Vproptrader
zip -r mt5_ea_corrected.zip mt5_ea/
```

Then download `mt5_ea_corrected.zip` using your file manager or WinSCP.

---

## 🚀 Method 2: Use WinSCP

1. Open WinSCP
2. Connect to: `3.111.22.56`
3. Navigate to: `/home/ubuntu/Sandeep/projects/Vproptrader/mt5_ea/`
4. Select all files
5. Drag to Windows Experts folder

---

## ✅ After Copying

1. **Open MetaEditor**
2. Press **F5** to refresh
3. Open **QuantSupraAI.mq5**
4. Press **F7** to compile
5. Should see: **"0 error(s), 0 warning(s)"** ✅

---

## 🔧 What Was Fixed

The corrected version has:
- ✅ Struct `SignalData` moved to top of file
- ✅ Module instances changed to pointers
- ✅ Proper initialization with `new` keyword
- ✅ Proper cleanup with `delete` keyword
- ✅ Removed duplicate functions
- ✅ Fixed constructor calls

---

## ⚠️ Important

**DO NOT edit the .mq5 file on Windows!** Always edit on Ubuntu and copy to Windows.

The Ubuntu version is the source of truth.

---

Ready to copy the files?
