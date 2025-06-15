import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import seaborn as sns
import requests

# Define Sophia panels and general test categories
sophia_panels = {
    # SOPHiA-specific
    "Solid Tumor – DNA Panel (325 genes)": 325,
    "Solid Tumor – RNA Panel (50 genes)": 50,
    "Solid Tumor – DNA + RNA Panel (375 genes)": 375,
    "Hematologic – DNA Panel (65 genes)": 65,
    "Hematologic – RNA Panel (50 genes)": 50,
    "Hematologic – DNA + RNA Panel (115 genes)": 115,
    "Liquid Biopsy – ctDNA (500 genes)": 500,
    "Germline – Hereditary Cancer Panel (47 genes)": 47,
    "Germline – Cardiovascular/Metabolic Panel (60 genes)": 60,
    "Germline – Pediatric/Undiagnosed Disease Panel (160 genes)": 160,
    # General categories
    "General – Solid Tumor DNA Panel (<50 genes)": 45,
    "General – Solid Tumor RNA Panel (<50 genes)": 40,
    "General – Solid Tumor DNA+RNA Panel (<100 genes)": 90,
    "General – Heme DNA Panel (<50 genes)": 48,
    "General – Heme RNA Panel (<50 genes)": 45,
    "General – Heme DNA+RNA Panel (<100 genes)": 95,
    "General – Germline Panel (<50 genes)": 40,
    "General – Germline Panel (50-100 genes)": 75,
    "General – Germline Panel (>100 genes)": 150
}

# Risk thresholds and billing notes
risk_notes = {
    # Germline
    "General – Germline Panel (50-100 genes)": {
        "risk_level": "Medium",
        "billing_note": "Consider billing with 81455. Denial risk may increase if policy requires <50 genes. Ensure strong documentation of medical necessity."
    },
    "General – Germline Panel (>100 genes)": {
        "risk_level": "High",
        "billing_note": "Most commercial payers do not cover panels >50 genes. Must use 81455. Recommend Z-code registration and MAC pre-check."
    },
    # Solid Tumor
    "Solid Tumor – DNA Panel (325 genes)": {
        "risk_level": "High",
        "billing_note": "Panels >300 genes typically require billing with 81455. Ensure strong rationale and clinical documentation to justify extent of profiling."
    },
    "Solid Tumor – DNA + RNA Panel (375 genes)": {
        "risk_level": "High",
        "billing_note": "High complexity assay – may not be reimbursed by all commercial payers. Use 81455 and document clearly why combined profiling was medically necessary."
    },
    # Liquid Biopsy
    "Liquid Biopsy – ctDNA (500 genes)": {
        "risk_level": "Very High",
        "billing_note": "Very few payers reimburse for ctDNA panels >300 genes. Consider alternatives or seek pre-authorization. Billing typically requires 81455."
    }
}

# Add filter for risk level
filter_risk = st.multiselect("Filter panels by risk level:", options=["Low", "Medium", "High", "Very High"])

# Filter panel list if filter applied
filtered_panels = [panel for panel in sophia_panels.keys()
                   if not filter_risk or risk_notes.get(panel, {}).get("risk_level") in filter_risk]

# Display risk notes in UI
selected_panel = st.selectbox("Select a test panel:", filtered_panels)

# Display color-coded badge with risk level
if selected_panel in risk_notes:
    risk_level = risk_notes[selected_panel]['risk_level']
    badge_color = {
        "Low": "✅",
        "Medium": "🟡",
        "High": "🔴",
        "Very High": "🚨"
    }.get(risk_level, "⚠️")
    st.markdown(f"### {badge_color} **Risk Level: {risk_level}**")
    st.info(risk_notes[selected_panel]['billing_note'])

# Step 7: Billing Documentation Section
st.markdown("### Step 7: Billing Documentation Guidance")
if selected_panel in risk_notes:
    st.markdown(f"**{selected_panel}** → {risk_notes[selected_panel]['billing_note']}")
else:
    st.markdown("Standard documentation applies based on test type and payer policies.\nPlease refer to Z-code and MAC-specific requirements if applicable.")
