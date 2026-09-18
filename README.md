# SnapSplit — Receipt Scanner & Expense Extractor (MVP)

A Streamlit MVP that lets a user upload a photo of a receipt, extracts
vendor / date / category / total, lets them correct any field in an
editable table, exports to CSV, and includes a simple cost-split
calculator for roommates.

Built to match the feature tiers from the MVP planning lab:

| Tier | Feature | Status |
|---|---|---|
| Must-Have | Photo upload | ✅ built |
| Must-Have | Extraction (vendor/date/category/total) | ✅ built |
| Must-Have | Editable results table | ✅ built |
| Must-Have | CSV export | ✅ built |
| Nice-to-Have | Split-cost calculator | ✅ built |
| Nice-to-Have | Spending chart | ✅ built |
| Next Version | User accounts / login | ❌ not built (by design) |
| Next Version | Bank/email auto-import | ❌ not built (by design) |

If the OCR engine (Tesseract) isn't installed in the environment, the app
detects this automatically and falls back to **Demo Mode**: photo upload
still works and previews the image, but field extraction is done through
the manual-entry form instead of crashing.

---

## 1. Run it locally in VS Code

**Requirements:** Python 3.9+ and VS Code with the Python extension installed.

1. Unzip this project and open the folder in VS Code:
   `File > Open Folder...` → select the unzipped `receipt_app` folder.

2. Open a terminal in VS Code (`` Ctrl+` `` / `` Cmd+` ``) and create a
   virtual environment:

   ```bash
   python -m venv venv
   ```

   Activate it:

   ```bash
   # macOS / Linux
   source venv/bin/activate

   # Windows (PowerShell)
   venv\Scripts\Activate.ps1
   ```

   In VS Code, also select this interpreter: `Ctrl+Shift+P` →
   `Python: Select Interpreter` → choose the `venv` one.

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. (Optional, for OCR) Install the Tesseract binary — this is a system
   package, separate from the `pytesseract` Python wrapper already in
   `requirements.txt`:

   - **macOS:** `brew install tesseract`
   - **Windows:** install from
     [UB-Mannheim/tesseract](https://github.com/UB-Mannheim/tesseract/wiki),
     then make sure the install folder is on your `PATH`.
   - **Linux (Debian/Ubuntu):** `sudo apt-get install tesseract-ocr`

   Without this step, the app still runs — photo extraction just falls
   back to manual entry (see Demo Mode above).

5. Run the app:

   ```bash
   streamlit run app.py
   ```

   VS Code will show a clickable `http://localhost:8501` link in the
   terminal — click it (or open it in a browser) to use the app.

---

## 2. Deploy it (Streamlit Community Cloud)

This is the fastest way to get a public, "already deployed" link:

1. Push this folder to a **public GitHub repository** (include
   `app.py`, `requirements.txt`, `packages.txt`, and `.streamlit/config.toml`).
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in
   with GitHub.
3. Click **New app**, pick the repo/branch, set the main file path to
   `app.py`, and click **Deploy**.
4. Streamlit Cloud automatically reads `requirements.txt` for Python
   packages and `packages.txt` for system packages (this is what
   installs Tesseract so OCR works on the deployed version, not just
   locally).

You'll get a public URL like `https://<your-app-name>.streamlit.app`
to submit.

---

## Project structure

```
receipt_app/
├── app.py                    # Main Streamlit app
├── requirements.txt          # Python dependencies
├── packages.txt              # System dependency (tesseract-ocr) for cloud deploys
├── .streamlit/
│   └── config.toml           # App theme/server config
└── README.md                 # This file
```

## Notes for grading / demo

- No API keys or paid services are required — extraction runs locally
  via Tesseract OCR plus lightweight regex parsing, so the demo works
  offline and without a budget, matching the MVP constraints from the
  planning lab (2-week solo build, no paid APIs).
- The **Split Costs** and **spending-by-category chart** are the
  nice-to-have features called out in the prioritization step; they're
  included but kept simple on purpose so they didn't take time away
  from the must-have extraction flow.
