# ZKAccess Complete - Installation Guide

## 🚀 Quick Installation (5 Minutes)

### Prerequisites
- Home Assistant 2024.1.0 or newer
- HACS installed (recommended)
- Network access to your C3-400 panels
- Panel IP addresses

---

## Method 1: HACS Installation (Recommended)

### Step 1: Add Custom Repository
1. Open **HACS** in Home Assistant
2. Click on **Integrations**
3. Click the **⋮** menu (top right corner)
4. Select **Custom repositories**
5. Add repository:
   ```
   URL: https://github.com/btzll1412/zkaccess-complete
   Category: Integration
   ```
6. Click **Add**

### Step 2: Install Integration
1. In HACS, search for **"ZKAccess Complete"**
2. Click on it
3. Click **Download**
4. Select latest version
5. Click **Download** again

### Step 3: Restart Home Assistant
```yaml
Settings → System → Restart
```

### Step 4: Add Integration
1. Go to **Settings → Devices & Services**
2. Click **+ Add Integration** (bottom right)
3. Search for **"ZKAccess Complete"**
4. Enter your panel details:
   - **Panel Name**: "Building A Main" (friendly name)
   - **IP Address**: 192.168.1.100
   - **Port**: 4370 (default)
   - **Password**: (leave blank if not set)
5. Click **Submit**

### Step 5: Access Dashboard
1. Check the sidebar - you'll see **"Access Control"** 🔐
2. Click it to open the beautiful dashboard!

---

## Method 2: Manual Installation

### Step 1: Download Files
```bash
# Option A: Clone repository
cd /config
git clone https://github.com/yourusername/zkaccess-complete.git
cp -r zkaccess-complete/custom_components/zkaccess_complete custom_components/

# Option B: Download ZIP
# Download from GitHub releases
# Extract to /config/custom_components/zkaccess_complete/
```

### Step 2: Verify Installation
Your folder structure should look like:
```
/config/
  └── custom_components/
      └── zkaccess_complete/
          ├── __init__.py
          ├── manifest.json
          ├── config_flow.py
          ├── const.py
          ├── coordinator.py
          ├── lock.py
          ├── services.py
          ├── api/
          │   └── c3_client.py
          └── frontend/
              └── zkaccess-panel.html
```

### Step 3: Restart & Configure
Follow steps 3-5 from Method 1 above.

---

## 📝 First-Time Setup

### Add Your Panels

For **single location** (1-2 panels):
```yaml
Panel 1: Main Building
  IP: 192.168.1.100
  Doors: 4
  
Panel 2: Annex Building
  IP: 192.168.1.101
  Doors: 4
```

For **multiple locations** (3+ panels):
```yaml
# Building A
Panel A1: 192.168.1.100 (4 doors)
Panel A2: 192.168.1.101 (4 doors)

# Building B
Panel B1: 192.168.2.100 (4 doors)
Panel B2: 192.168.2.101 (4 doors)

# Building C
Panel C1: 192.168.3.100 (4 doors)
```

### Configure Options

After adding each panel, click **Configure**:

| Option | Recommended | Description |
|--------|-------------|-------------|
| Scan Interval | 5 seconds | How often to check for events |
| Unlock Duration | 5 seconds | Default unlock time |
| Enable Notifications | Yes | Get alerts for important events |

---

## 👤 Add Your First User

### Via Dashboard (Easy!)

1. Open **Access Control** from sidebar
2. Click **Users** tab
3. Click **+ Add User** button
4. Fill in the form:

```yaml
Name: John Doe
Employee ID: EMP001
Verification Mode: Card AND PIN
Card Number: 123456789
PIN Code: 1234
Groups: [Employees]
Status: Active
```

5. Click **Save**

The user is now synced to ALL your panels automatically! 🎉

### Via Service Call (Advanced)

```yaml
service: zkaccess_complete.add_user
data:
  user_name: "John Doe"
  card_number: "123456789"
  pin_code: "1234"
  verify_mode: "card_and_pin"
  groups: ["employees"]
```

---

## 🔐 Create Access Groups

### Step 1: Define Groups

1. Go to **Access Groups** tab
2. Click **+ New Group**

**Example Groups:**

```yaml
Group 1: Employees
  - Doors: 1, 2, 3, 5, 6
  - Schedule: Business Hours
  - Users: 150
  
Group 2: Managers
  - Doors: All (1-8)
  - Schedule: Extended Hours
  - Users: 25
  
Group 3: Contractors
  - Doors: 1, 5
  - Schedule: Contractor Hours
  - Users: 25
```

### Step 2: Assign Users
When adding/editing users, select which groups they belong to.

---

## 📅 Set Up Schedules

### Create Time Zones

```yaml
Business Hours:
  Monday-Friday: 8:00 AM - 6:00 PM
  Saturday-Sunday: Closed
  
Extended Hours:
  Monday-Saturday: 6:00 AM - 10:00 PM
  Sunday: Closed
  
24/7 Access:
  All Days: 00:00 - 23:59
```

### Assign to Groups
Link time zones to access groups for automatic enforcement.

---

## 🎯 Test Everything

### Test Door Control

1. **Via Dashboard:**
   - Click on any door card
   - Click "Unlock" button
   - Door should unlock for configured duration

2. **Via Entity:**
   ```yaml
   # Developer Tools → Services
   service: lock.unlock
   target:
     entity_id: lock.main_entrance
   ```

### Test User Access

1. Have user swipe card or enter PIN
2. Check **Live Events** tab
3. Should see access granted event
4. Get notification (if enabled)

### Test Services

```yaml
# Lock all doors
service: zkaccess_complete.lock_all_doors

# Unlock specific doors
service: zkaccess_complete.unlock_all_doors
data:
  only_doors: [1, 2]
  duration: 10
```

---

## 🔧 Troubleshooting

### Can't Add Integration

**Error:** "Cannot connect to panel"

**Solutions:**
1. Verify IP address: `ping 192.168.1.100`
2. Check port: `nc -zv 192.168.1.100 4370`
3. Verify panel is on network
4. Check firewall rules
5. Try panel reboot

### No Events Showing

**Solutions:**
1. Check scan interval in options
2. Verify network connection
3. Reload integration
4. Check Home Assistant logs:
   ```yaml
   Settings → System → Logs
   Filter: "zkaccess"
   ```

### Users Not Syncing

**Solutions:**
1. Verify panel is online (Dashboard → System)
2. Check user data format
3. Manual sync:
   ```yaml
   service: zkaccess_complete.sync_all_users
   ```

### Dashboard Not Loading

**Solutions:**
1. Clear browser cache
2. Hard refresh: Ctrl + F5 (Windows) / Cmd + Shift + R (Mac)
3. Try different browser
4. Check browser console for errors

---

## 📊 Verify Installation

### Check These Items:

✅ Integration appears in Devices & Services  
✅ "Access Control" appears in sidebar  
✅ Dashboard loads with all tabs  
✅ Entities created for each door  
✅ Services available in Developer Tools  
✅ Events showing in Live Events tab  
✅ Can lock/unlock doors  
✅ Notifications working  

---

## 🎓 Next Steps

### Learn More
- Read the [README](README.md) for complete feature list
- Check [Automation Examples](README.md#example-automations)
- Explore all dashboard tabs
- Review service documentation

### Customize
- Add more panels
- Create custom access groups
- Set up automations
- Configure notifications
- Design your schedules

### Get Help
- [GitHub Issues](https://github.com/btzll1412/zkaccess-complete/issues)
- [Community Forum](https://community.home-assistant.io)
- [Discord](https://discord.gg/example)

---

## 🎉 You're All Set!

You now have a professional access control system running in Home Assistant!

### What You Can Do Now:
- ✅ Manage 200+ users
- ✅ Control 8-40 doors
- ✅ Monitor live events
- ✅ Generate reports
- ✅ Create automations
- ✅ Set up schedules
- ✅ Grant temporary access

### Remember:
- **Everything works offline** - panels are independent
- **Real-time monitoring** - see events as they happen
- **Fully integrated** - works with all HA features
- **Extensible** - request features anytime!

---

**Enjoy your new access control system! 🚀**

*Need help? Open an issue or start a discussion on GitHub!*
