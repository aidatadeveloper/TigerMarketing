# Tiger Marketing - Project Instructions

## Overview
Marketing platform targeting businesses around Auburn University ("Home of the Tigers"). Built to pull business data, manage outreach campaigns, and track marketing efforts.

## Database: TIGER_MARKETING (SQL Server localhost, Windows Auth)

### Tables
| Table | Purpose |
|-------|---------|
| BUSINESSES | All businesses around Auburn University (from OpenStreetMap + Google) |
| CAMPAIGNS | Marketing campaigns linked to businesses |
| CONTACTS | Contact info for business owners/managers |

### Connection
```python
import pyodbc
conn = pyodbc.connect('DRIVER={SQL Server};SERVER=localhost;DATABASE=TIGER_MARKETING;Trusted_Connection=yes;', timeout=30)
```

```cmd
sqlcmd -S localhost -d TIGER_MARKETING -E -Q "YOUR_QUERY"
```

## Project Structure
```
C:\My Projects\Python\TigerMarketing\
├── CLAUDE.md           # This file
├── logs/               # Script logs
├── scripts/            # Python scripts
├── data/               # CSV exports, reports
├── images/             # Business photos (Street View, etc.)
```

## Related Work
- auburn_businesses/ folder has initial 345 business pull from OpenStreetMap Overpass API
- Google Street View image downloads (requires API key)
