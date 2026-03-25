# DT-STENO — Private Steno Institute Platform

## Tech Stack
- **Backend**: Python Flask
- **Database**: Google Sheets (via gspread)
- **Hosting**: Render.com (free tier)
- **Theme**: Dark Navy + Gold

---

## Google Sheets Setup

Create a spreadsheet named exactly: `DT-STENO_DB`

Add these tabs (exact names):

### Students
| StudentID | Name | Mobile | Email | Password | ClassCode | Approved | JoinedDate | Batch |

### Passages
| PassageCode | PassageName | Category | Speed | Passage | TotalWords | Active | AudioLink |

### Attempts
| AttemptID | StudentID | PassageCode | TestID | TimeTaken | TypedWords | WPM | FullMistakes | HalfMistakes | Omissions | ExtraWords | Capitalization | FullStop | TotalErrors | ErrorPercent | Mode | Date | HighlightedPassage | AdminNote | Corrected |

### Tests
| TestID | PassageCode | AudioLink | CreatedBy | CreatedAt | ExpiresAt | Active | AllowedStudents | TimeLimitMinutes | Notes |

### Settings
| Key | Value |

Add first row in Settings:
- Key: `CLASS_CODE`  Value: `STENO2024` (change this to your secret code)

---

## Local Setup

```bash
# 1. Clone / copy files to your project folder
# 2. Create virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Add your service_account.json (Google API credentials)
#    Place it in the root folder

# 5. Run locally
python app.py
# Open http://localhost:5000
```

---

## Deploy on Render.com (Free — No Domain Purchase Needed)

1. Push code to GitHub (private repo)
2. Go to https://render.com → New Web Service
3. Connect your GitHub repo
4. Settings:
   - **Build command**: `pip install -r requirements.txt`
   - **Start command**: `gunicorn app:create_app() --bind 0.0.0.0:$PORT`
   - **Environment variables**:
     - `SECRET_KEY` = any long random string
     - `ADMIN_PASSWORD` = your admin password
5. Add your `service_account.json` content as an environment variable:
   - `GOOGLE_CREDENTIALS` = paste entire JSON content
6. Deploy → Get your URL like `dt-steno.onrender.com`
7. Share this URL with your students via WhatsApp

---

## Usage

### Admin Panel
- URL: `your-url.onrender.com/admin/login`
- Default password: `admin123` (change via ADMIN_PASSWORD env var)

### Admin Workflow
1. **Add passages** → Admin → Passages → Add Passage (with category, speed, audio link)
2. **Create test** → Admin → Tests → Create Test → Copy test link → Send via WhatsApp
3. **Review attempts** → Admin → Attempts → click any attempt → correct scores if needed
4. **Monthly report** → Admin → Reports → select month

### Student Workflow
1. Receive class code from instructor
2. Register at `your-url/register`
3. Wait for instructor approval
4. Login → Dashboard → see active tests or browse passage library
5. Click test link from WhatsApp → enter passage code if needed → transcribe → submit

### Saturday Test Workflow
1. Admin creates test with passage code + Google Drive audio link
2. Copies test link (e.g. `your-url/student/test/TST1A2B3C`)
3. Sends link via WhatsApp: "Saturday test: [link] — Audio: [drive link]"
4. Student opens audio on phone, opens test link on PC
5. Transcribes and submits
6. Admin reviews results in Admin → Tests → [test ID]

---

## File Structure
```
dt-steno/
├── app.py                    # Main Flask app
├── requirements.txt
├── service_account.json      # Google API (DO NOT commit to GitHub)
├── auth/
│   └── routes.py             # Login, register, logout
├── student/
│   └── routes.py             # Student dashboard, practice, test, history
├── admin/
│   └── routes.py             # Admin panel all routes
├── database/
│   └── db.py                 # Google Sheets DB layer
├── engine/
│   └── evaluator.py          # Error evaluation engine
├── static/
│   └── css/main.css          # Design system
└── templates/
    ├── landing.html           # Public homepage
    ├── login.html
    ├── register.html
    ├── student/
    │   ├── dashboard.html
    │   ├── passages.html
    │   ├── practice.html
    │   ├── test_entry.html
    │   ├── test.html
    │   ├── attempt_result.html
    │   ├── history.html
    │   └── leaderboard.html
    └── admin/
        ├── login.html
        ├── dashboard.html
        ├── students.html
        ├── student_profile.html
        ├── passages.html
        ├── tests.html
        ├── test_detail.html
        ├── attempts.html
        ├── attempt_detail.html
        ├── monthly_report.html
        ├── student_report.html
        ├── evaluate.html
        └── settings.html
```

---

## Passage Categories
- `KC` — Kailash Chandra passages
- `TN_DOTE` — Tamil Nadu DOTE passages
- `Pitman` — Pitman basic lessons
- `General` — General passages
- `Legal` — Legal/Presidential speeches

## Error Types (Evaluation)
- **Full mistake** = completely wrong word (counts as 1 error)
- **Half mistake** = close variant / minor error (counts as 0.5)
- **Omission** = word missing (counts as 1)
- **Extra word** = extra word typed (counts as 0.5)
- **Capitalisation** = wrong case (counts as 0.5)
- **Full stop** = punctuation error (counts as 0.5)
- **Pass** = error% ≤ 5%

---

*Private platform — not for public use*
