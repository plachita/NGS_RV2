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

# CPT code mapping logic
cpt_mapping = {
    "<50": "81450",
    "50-100": "81455",
    ">100": "81455"
}

panel_gene_count = sophia_panels[selected_panel]
if panel_gene_count <= 50:
    suggested_cpt = cpt_mapping["<50"]
elif 50 < panel_gene_count <= 100:
    suggested_cpt = cpt_mapping["50-100"]
else:
    suggested_cpt = cpt_mapping[">100"]

st.markdown(f"### CPT Code Recommendation: **{suggested_cpt}**")

# Profitability & ROI simulation (simplified)
st.markdown("### Step 8: Backbone Strategy Analysis")
st.write("If using an exome/genome as a backbone, estimate minimum carve-out panels needed for profitability:")

cost_per_backbone = st.number_input("Cost per exome/genome backbone ($):", min_value=0, value=728)
price_per_panel = st.number_input("Reimbursed amount per carved-out panel ($):", min_value=0, value=600)
backbone_reimbursed = st.number_input("Optional: Reimbursed amount for backbone ($, if billed):", min_value=0, value=0)

if price_per_panel > 0:
    if backbone_reimbursed > 0:
        needed_panels = max(1, round((cost_per_backbone - backbone_reimbursed) / price_per_panel + 1))
        st.success(f"▶️ To break even: **{needed_panels}** carved-out panel(s) needed per exome/genome **after backbone reimbursement**.")
    else:
        needed_panels = round(cost_per_backbone / price_per_panel + 1)
        st.warning(f"⚠️ To break even (if backbone is not billed): **{needed_panels}** carved-out panel(s) needed per genome/exome.")
else:
    st.error("Panel reimbursement must be greater than $0.")

# ROI Visualization
st.markdown("### ROI Visualization")
tests = list(range(1, needed_panels + 5))
roi_values = [((price_per_panel * n) + backbone_reimbursed - cost_per_backbone) for n in tests]

fig, ax = plt.subplots()
ax.plot(tests, roi_values, marker='o')
ax.axhline(0, color='gray', linestyle='--')
ax.set_xlabel("# Carve-out Panels per Exome/Genome")
ax.set_ylabel("Net Profit ($)")
ax.set_title("ROI vs. Number of Carve-out Panels")

st.pyplot(fig)

# Export button
st.markdown("### Download Summary")
data = {
    "Selected Test": selected_panel,
    "Gene Count": panel_gene_count,
    "Risk Level": risk_notes.get(selected_panel, {}).get("risk_level", "N/A"),
    "Suggested CPT Code": suggested_cpt,
    "Break-even Panels (No Backbone Reimbursement)": round(cost_per_backbone / price_per_panel + 1),
    "Break-even Panels (With Backbone Reimbursement)": max(1, round((cost_per_backbone - backbone_reimbursed) / price_per_panel + 1))
}
df_export = pd.DataFrame([data])

buffer = BytesIO()
df_export.to_excel(buffer, index=False, engine='openpyxl')
buffer.seek(0)
st.download_button(
    label="📥 Download Reimbursement Summary (Excel)",
    data=buffer,
    file_name="ngs_reimbursement_summary.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
