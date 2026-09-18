"""
SnapSplit — Receipt Scanner & Expense Extractor (MVP)
------------------------------------------------------
A lightweight Streamlit app that lets a user upload a photo of a receipt,
extracts structured data (vendor, date, total, category) from it, lets
the user correct any field in an editable table, and exports the result
to CSV. Includes a simple cost-splitting calculator as a nice-to-have.

This matches the MVP scope defined in the planning lab:
  Must-Have   : photo upload, extraction, editable results table, CSV export
  Nice-to-Have: split-cost calculator, spending chart
  Next Version: accounts/login, bank/email auto-import (not built here)
"""

import io
import re
import uuid
from datetime import date, datetime

import pandas as pd
import streamlit as st

# --------------------------------------------------------------------------
# Optional OCR backend. The app runs in full "Demo Mode" (manual entry only)
# if Tesseract / pytesseract aren't available in the deployment environment,
# so it never crashes on a machine that hasn't installed the OS-level
# Tesseract binary.
# --------------------------------------------------------------------------
try:
    import pytesseract
    from PIL import Image

    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False


# --------------------------------------------------------------------------
# Page setup
# --------------------------------------------------------------------------
st.set_page_config(
    page_title="SnapSplit — Receipt Scanner",
    page_icon="🧾",
    layout="wide",
)

if "receipts" not in st.session_state:
    # Each row: id, vendor, date, category, total, source
    st.session_state.receipts = pd.DataFrame(
        columns=["id", "vendor", "date", "category", "total", "source"]
    )


# --------------------------------------------------------------------------
# Extraction helpers
# --------------------------------------------------------------------------
CATEGORY_KEYWORDS = {
    "Groceries": ["market", "grocery", "foods", "mart", "supermarket"],
    "Dining": ["cafe", "coffee", "restaurant", "grill", "diner", "pizza", "bar"],
    "Transport": ["uber", "lyft", "taxi", "gas", "fuel", "transit", "parking"],
    "Utilities": ["electric", "water", "internet", "utility", "utilities"],
    "Shopping": ["store", "shop", "mall", "retail"],
}


def guess_category(vendor_text: str) -> str:
    text = (vendor_text or "").lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            return category
    return "Other"


def extract_total(raw_text: str):
    """Find the most likely 'total' amount in OCR'd receipt text."""
    candidates = []
    for line in raw_text.splitlines():
        line_lower = line.lower()
        match = re.search(r"(\d+[.,]\d{2})", line)
        if match:
            amount = float(match.group(1).replace(",", "."))
            weight = 2 if "total" in line_lower and "sub" not in line_lower else 1
            candidates.append((weight, amount))
    if not candidates:
        return None
    candidates.sort(key=lambda x: (x[0], x[1]))
    return candidates[-1][1]


def extract_date(raw_text: str):
    patterns = [
        r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
        r"(\d{4}[/-]\d{1,2}[/-]\d{1,2})",
    ]
    for pattern in patterns:
        match = re.search(pattern, raw_text)
        if match:
            for fmt in ("%m/%d/%Y", "%m/%d/%y", "%m-%d-%Y", "%Y-%m-%d", "%Y/%m/%d"):
                try:
                    return datetime.strptime(match.group(1), fmt).date()
                except ValueError:
                    continue
    return date.today()


def extract_vendor(raw_text: str):
    for line in raw_text.splitlines():
        cleaned = line.strip()
        if len(cleaned) >= 3 and not re.search(r"\d{2}[/-]\d{2}", cleaned):
            return cleaned[:40]
    return "Unknown vendor"


def run_extraction(image_bytes: bytes):
    """Returns a dict of extracted fields from an uploaded receipt image."""
    if not OCR_AVAILABLE:
        return None
    image = Image.open(io.BytesIO(image_bytes))
    raw_text = pytesseract.image_to_string(image)
    vendor = extract_vendor(raw_text)
    return {
        "vendor": vendor,
        "date": extract_date(raw_text),
        "category": guess_category(vendor),
        "total": extract_total(raw_text) or 0.0,
    }


def add_receipt(vendor, receipt_date, category, total, source):
    new_row = pd.DataFrame(
        [
            {
                "id": uuid.uuid4().hex[:8],
                "vendor": vendor,
                "date": receipt_date,
                "category": category,
                "total": round(float(total), 2),
                "source": source,
            }
        ]
    )
    st.session_state.receipts = pd.concat(
        [st.session_state.receipts, new_row], ignore_index=True
    )


# --------------------------------------------------------------------------
# Sidebar
# --------------------------------------------------------------------------
with st.sidebar:
    st.title("🧾 SnapSplit")
    st.caption("Receipt scanning MVP — plan-to-build lab")
    st.markdown("---")
    st.markdown("**Status**")
    st.write("OCR engine:", "✅ available" if OCR_AVAILABLE else "⚠️ not installed (Demo Mode)")
    if not OCR_AVAILABLE:
        st.info(
            "Tesseract isn't installed in this environment, so photo "
            "extraction falls back to manual entry. See README.md to "
            "enable OCR locally or on Streamlit Cloud."
        )
    st.markdown("---")
    st.markdown("**MVP scope**")
    st.markdown(
        "- ✅ Photo upload\n"
        "- ✅ Extraction (vendor / date / category / total)\n"
        "- ✅ Editable results table\n"
        "- ✅ CSV export\n"
        "- ✅ Split-cost calculator (nice-to-have)\n"
    )


# --------------------------------------------------------------------------
# Main layout
# --------------------------------------------------------------------------
st.title("SnapSplit: Snap a receipt, get a structured expense")

tab_scan, tab_table, tab_split = st.tabs(
    ["📷 Scan a Receipt", "📋 Expense Table", "🤝 Split Costs"]
)

# ---------------------------------------------------------------- Tab 1 ---
with tab_scan:
    st.subheader("Upload a receipt")
    col_upload, col_manual = st.columns(2)

    with col_upload:
        st.markdown("**Option A — Photo upload**")
        uploaded_file = st.file_uploader(
            "Upload a receipt photo", type=["png", "jpg", "jpeg"]
        )
        if uploaded_file is not None:
            st.image(uploaded_file, caption="Uploaded receipt", width=260)
            if st.button("Extract data from photo", type="primary"):
                image_bytes = uploaded_file.getvalue()
                result = run_extraction(image_bytes)
                if result is None:
                    st.warning(
                        "OCR isn't available in this environment, so nothing "
                        "was auto-filled. Use manual entry on the right, or "
                        "install Tesseract locally (see README.md)."
                    )
                else:
                    st.session_state["last_extraction"] = result
                    st.success("Extraction complete — review the fields below.")

        extraction = st.session_state.get("last_extraction")
        if extraction:
            st.markdown("**Review extracted fields**")
            v = st.text_input("Vendor", value=extraction["vendor"], key="ext_vendor")
            d = st.date_input("Date", value=extraction["date"], key="ext_date")
            c = st.selectbox(
                "Category",
                list(CATEGORY_KEYWORDS.keys()) + ["Other"],
                index=(list(CATEGORY_KEYWORDS.keys()) + ["Other"]).index(
                    extraction["category"]
                ),
                key="ext_category",
            )
            t = st.number_input(
                "Total ($)", min_value=0.0, value=float(extraction["total"]), step=0.01,
                key="ext_total",
            )
            if st.button("Add to expense table"):
                add_receipt(v, d, c, t, source="photo")
                st.session_state.pop("last_extraction", None)
                st.success("Added! Check the Expense Table tab.")
                st.rerun()

    with col_manual:
        st.markdown("**Option B — Manual entry**")
        st.caption("Always available, no photo or OCR required.")
        with st.form("manual_entry_form", clear_on_submit=True):
            m_vendor = st.text_input("Vendor", placeholder="e.g., Campus Cafe")
            m_date = st.date_input("Date", value=date.today())
            m_category = st.selectbox(
                "Category", list(CATEGORY_KEYWORDS.keys()) + ["Other"]
            )
            m_total = st.number_input("Total ($)", min_value=0.0, step=0.01)
            submitted = st.form_submit_button("Add to expense table", type="primary")
            if submitted:
                if not m_vendor:
                    st.error("Vendor name is required.")
                else:
                    add_receipt(m_vendor, m_date, m_category, m_total, source="manual")
                    st.success("Added! Check the Expense Table tab.")

# ---------------------------------------------------------------- Tab 2 ---
with tab_table:
    st.subheader("Expense table")
    if st.session_state.receipts.empty:
        st.info("No expenses yet — add one from the Scan a Receipt tab.")
    else:
        edited = st.data_editor(
            st.session_state.receipts,
            column_config={
                "id": st.column_config.TextColumn("ID", disabled=True),
                "vendor": st.column_config.TextColumn("Vendor"),
                "date": st.column_config.DateColumn("Date"),
                "category": st.column_config.SelectboxColumn(
                    "Category", options=list(CATEGORY_KEYWORDS.keys()) + ["Other"]
                ),
                "total": st.column_config.NumberColumn("Total ($)", format="$%.2f"),
                "source": st.column_config.TextColumn("Source", disabled=True),
            },
            num_rows="dynamic",
            use_container_width=True,
            hide_index=True,
            key="expense_editor",
        )
        st.session_state.receipts = edited

        col_a, col_b, col_c = st.columns(3)
        col_a.metric("Total spent", f"${edited['total'].sum():,.2f}")
        col_b.metric("Receipts logged", len(edited))
        col_c.metric(
            "Avg. per receipt",
            f"${edited['total'].mean():,.2f}" if len(edited) else "$0.00",
        )

        st.markdown("**Spending by category**")
        if not edited.empty:
            by_cat = edited.groupby("category")["total"].sum().sort_values(ascending=False)
            st.bar_chart(by_cat)

        csv_bytes = edited.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Export to CSV",
            data=csv_bytes,
            file_name="expenses.csv",
            mime="text/csv",
            type="primary",
        )

# ---------------------------------------------------------------- Tab 3 ---
with tab_split:
    st.subheader("Split costs with roommates")
    st.caption("Nice-to-have feature from the MVP prioritization step.")

    if st.session_state.receipts.empty:
        st.info("Add expenses first, then come back here to split them.")
    else:
        total_spent = st.session_state.receipts["total"].sum()
        num_people = st.number_input(
            "Number of people splitting the bill", min_value=1, value=2, step=1
        )
        names_raw = st.text_input(
            "Names (comma-separated, optional)", placeholder="e.g., Alex, Sam, Jordan"
        )

        per_person = total_spent / num_people if num_people else 0
        st.metric("Total to split", f"${total_spent:,.2f}")
        st.metric("Each person owes", f"${per_person:,.2f}")

        names = [n.strip() for n in names_raw.split(",") if n.strip()]
        if names:
            split_df = pd.DataFrame(
                {"Person": names, "Owes": [round(per_person, 2)] * len(names)}
            )
            st.table(split_df)

st.markdown("---")
st.caption(
    "SnapSplit MVP · built for the GenAI MVP Lab · "
    "must-have features are fully functional; nice-to-have and next-version "
    "features are scoped for future iterations."
)
