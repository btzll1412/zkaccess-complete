# ZKAccess Complete Control System

A complete, professional access control system for ZKTeco C3-100/200/400 panels integrated into Home Assistant.

![Dashboard](https://via.placeholder.com/800x400?text=ZKAccess+Dashboard)

## ✨ Features

### 🎯 Core Functionality
- ✅ **Multi-Panel Support** - Manage unlimited C3 panels (8 to 40+ doors)
- ✅ **100% Offline Operation** - All access control runs on panels, works even if HA is down
- ✅ **Real-time Monitoring** - Live event feed with instant notifications
- ✅ **Beautiful Dashboard** - Modern, intuitive web interface

### 👥 User Management
- Add/Edit/Delete users with photos
- Card and PIN assignment
- Flexible verification modes:
  - Card Only
  - PIN Only
  - Card OR PIN
  - Card AND PIN
- User groups and access levels
- Temporary access (start/end dates)
- Bulk import from CSV
- 200+ users supported per panel (30,000 capacity)

### 🔐 Access Control
- Custom access groups
- Time-based access (schedules)
- Holiday management
- Multi-card unlock
- Anti-passback
- First card unlock
- Door-specific permissions

### 📊 Monitoring & Events
- Live event dashboard
- Real-time notifications
- Transaction history (100,000 events per panel)
- Event filtering and search
- Export to CSV/PDF
- Current occupancy tracking

### 🚪 Door Control
- Lock/Unlock individual doors
- Bulk lock/unlock operations
- Configurable unlock duration
- Door sensor monitoring
- Alarm management
- Auxiliary outputs control

## 📦 Installation

### Method 1: HACS (Recommended)

1. **Add Custom Repository**
   - Open HACS in Home Assistant
   - Click on "Integrations"
   - Click the three dots menu (top right)
   - Select "Custom repositories"
   - Add: "https://github.com/btzll1412/zkaccess-complete"`
   - Category: Integration
   - Click "Add"

2. **Install Integration**
   - Search for "ZKAccess Complete"
   - Click "Download"
   - Restart Home Assistant

### Method 2: Manual Installation

1. Download the latest release
2. Copy `custom_components/zkaccess_complete` to your Home Assistant `config/custom_components/` directory
3. Restart Home Assistant

## 🚀 Quick Start

### 1. Add Your First Panel

1. Go to **Settings → Devices & Services**
2. Click **+ Add Integration**
3. Search for **"ZKAccess Complete"**
4. Enter your panel details:
   - **Panel Name**: "Building A Main"
   - **IP Address**: 192.168.1.100
   - **Port**: 4370 (default)
   - **Password**: (if set)
5. Click **Submit**

### 2. Access the Dashboard

- Go to **Sidebar → Access Control**
- You'll see the beautiful dashboard with:
  - System statistics
  - Recent activity
  - Door status
  - Quick controls

### 3. Add Your First User

1. Click **Users** tab
2. Click **+ Add User**
3. Fill in details:
   - Name: "John Doe"
   - Card Number: 123456789
   - PIN: 1234
   - Verification Mode: Card + PIN
   - Groups: Employees
4. Click **Save**

The user is instantly synced to all your C3 panels!

## 🔧 Configuration

### Panel Options

Configure each panel's behavior:

```yaml
# Go to: Settings → Devices & Services → ZKAccess → Options

Scan Interval: 5 seconds (1-60)
Unlock Duration: 5 seconds (1-255)
Enable Notifications: true/false
```

### Creating Access Groups

1. Go to **Access Groups** tab
2. Click **+ New Group**
3. Configure:
   - Group Name: "Employees"
   - Select Doors: 1, 2, 3, 5, 6
   - Time Zones: "Business Hours"
4. Assign users to this group

### Setting Up Schedules

1. Go to **Schedules** tab
2. Click **+ New Schedule**
3. Define time ranges:
   - Name: "Business Hours"
   - Monday-Friday: 8:00 AM - 6:00 PM
   - Saturday-Sunday: Closed
4. Apply to access groups

## 🤖 Automations & Services

### Services Available

#### Lock/Unlock Doors

```yaml
# Unlock a specific door
service: zkaccess_complete.unlock_door
data:
  entity_id: lock.main_entrance
  duration: 10  # seconds

# Lock all doors
service: zkaccess_complete.lock_all_doors

# Unlock specific doors
service: zkaccess_complete.unlock_all_doors
data:
  only_doors: [1, 2]
  duration: 5
```

#### User Management

```yaml
# Add user
service: zkaccess_complete.add_user
data:
  user_name: "John Doe"
  card_number: "123456789"
  pin_code: "1234"
  verify_mode: "card_and_pin"
  groups: ["employees"]
  start_date: "2025-01-01"
  end_date: "2025-12-31"

# Update user
service: zkaccess_complete.update_user
data:
  user_id: 1
  groups: ["employees", "managers"]

# Delete user
service: zkaccess_complete.delete_user
data:
  user_id: 1
```

### Example Automations

#### Emergency Lockdown

```yaml
automation:
  - alias: "Emergency Lockdown"
    trigger:
      - platform: state
        entity_id: input_boolean.emergency_mode
        to: "on"
    action:
      - service: zkaccess_complete.lock_all_doors
      - service: notify.mobile_app
        data:
          message: "🚨 All doors locked - Emergency mode activated"
```

#### Welcome Notification

```yaml
automation:
  - alias: "Employee Welcome"
    trigger:
      - platform: event
        event_type: zkaccess_access_granted
        event_data:
          user_name: "John Doe"
          door: 1
    action:
      - service: notify.mobile_app
        data:
          message: "Welcome back, {{ trigger.event.data.user_name }}!"
```

#### After Hours Alert

```yaml
automation:
  - alias: "After Hours Access Alert"
    trigger:
      - platform: event
        event_type: zkaccess_access_granted
    condition:
      - condition: time
        after: "18:00:00"
        before: "06:00:00"
    action:
      - service: notify.security_team
        data:
          message: "After hours access: {{ trigger.event.data.user_name }} at {{ trigger.event.data.door_name }}"
```

## 📱 Mobile App Support

- Receive push notifications for important events
- View live event feed
- Lock/Unlock doors remotely
- Check door status
- Manage users on the go

## 🔒 Security

### Best Practices

1. **Network Security**
   - Put C3 panels on isolated VLAN
   - Use firewall rules
   - Enable panel passwords

2. **User Management**
   - Regular access audits
   - Remove expired users
   - Use strong PINs
   - Rotate cards periodically

3. **Backup**
   - Regular configuration backups
   - Export user database
   - Save audit logs

### Data Storage

- All configuration stored in Home Assistant
- User data encrypted at rest
- Events logged locally and on panels
- Backup survives Home Assistant restarts

## 📊 Supported Devices

| Model | Doors | Readers | Status |
|-------|-------|---------|--------|
| C3-100 | 1 | 2 | ✅ Tested |
| C3-200 | 2 | 4 | ✅ Tested |
| C3-400 | 4 | 4 | ✅ Tested |
| inBio 160 | 1 | 2 | ✅ Compatible |
| inBio 260 | 2 | 4 | ✅ Compatible |
| inBio 460 | 4 | 4 | ✅ Compatible |

## 🐛 Troubleshooting

### Can't Connect to Panel

```bash
# Check network connectivity
ping 192.168.1.100

# Verify port is open
nc -zv 192.168.1.100 4370

# Check Home Assistant logs
Settings → System → Logs
Filter: "zkaccess"
```

### Events Not Updating

1. Check scan interval (Settings → Options)
2. Verify network stability
3. Restart integration
4. Check panel firmware version

### User Not Syncing

1. Verify panel is online
2. Check user data format
3. View coordinator logs
4. Manually refresh data

## 🛠️ Advanced Configuration

### Multiple Buildings

```yaml
# Configure separate panels for different locations
Panel 1: Building A - IP: 192.168.1.100
Panel 2: Building B - IP: 192.168.2.100
Panel 3: Building C - IP: 192.168.3.100
```

### Custom Door Names

Edit in **System** tab to give doors friendly names:
- Door 1 → "Main Entrance"
- Door 2 → "Server Room"
- Door 3 → "Executive Office"

## 📝 Roadmap

### Coming Soon
- [ ] Visitor management
- [ ] Temporary QR codes
- [ ] Facial recognition integration
- [ ] License plate recognition
- [ ] Elevator control
- [ ] Active Directory sync
- [ ] Advanced analytics
- [ ] Mobile credentials
- [ ] REST API
- [ ] Webhook support

## 🤝 Contributing

We welcome contributions! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 💬 Support

-- **Issues**: [GitHub Issues](https://github.com/btzll1412/zkaccess-complete/issues)
- **Discussions**: [GitHub Discussions](https://github.com/btzll1412/zkaccess-complete/discussions)
## 🙏 Credits

- Based on ZKTeco C3 protocol
- Built for Home Assistant community
- Inspired by professional access control systems

---

**Made with ❤️ for the Home Assistant community**
