import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import seaborn as sns
import requests
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import base64

# --------------------------
# Sidebar Inputs
# --------------------------
st.sidebar.markdown("### Optional Inputs")
zip_code = st.sidebar.text_input("Enter ZIP Code (for future regional guidance):")
test_strategy = st.sidebar.radio("Test Strategy:", ["Panel Only", "Carve-out from WES", "Carve-out from WGS"])

# --------------------------
# Step 1: Select Test Type
# --------------------------
st.markdown("## Step 1: Select Test Type")
test_type = st.selectbox("Choose a test type:", [
    "Solid Tumor – DNA", "Solid Tumor – RNA", "Solid Tumor – DNA + RNA",
    "Hematologic – DNA", "Hematologic – RNA", "Hematologic – DNA + RNA",
    "Liquid Biopsy", "Germline", "WES (Whole Exome)", "WGS (Whole Genome)"
])

# --------------------------
# Step 2: Select Panel Source
# --------------------------
st.markdown("## Step 2: Select Panel Source")
panel_source = st.radio("Select source:", ["SOPHiA Genetics", "General Category"])

# --------------------------
# Step 3: Select Specific Panel
# --------------------------
st.markdown("## Step 3: Select Specific Panel")
sophia_panels = {
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
    "WES – SOPHiA Exome Backbone (19000 genes)": 19000,
    "WGS – SOPHiA Genome Backbone (20000+ genes)": 20000,
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

if test_type in ["WES (Whole Exome)", "WGS (Whole Genome)"]:
    available_panels = [p for p in sophia_panels.keys() if test_type.split(" ")[0] in p]
elif panel_source == "SOPHiA Genetics":
    available_panels = [p for p in sophia_panels.keys() if test_type.split(" –")[0] in p and "General" not in p]
elif panel_source == "General Category":
    available_panels = [p for p in sophia_panels.keys() if test_type.split(" –")[0] in p and "General" in p]
else:
    available_panels = list(sophia_panels.keys())

selected_panel = st.selectbox("Available Panels:", available_panels)

# --------------------------
# Step 4: Risk Filter
# --------------------------
st.markdown("## Step 4: Risk Filter")
risk_notes = {
    "General – Germline Panel (50-100 genes)": {
        "risk_level": "Medium",
        "billing_note": "Consider billing with 81455. Denial risk may increase if policy requires <50 genes. Ensure strong documentation of medical necessity."
    },
    "General – Germline Panel (>100 genes)": {
        "risk_level": "High",
        "billing_note": "Most commercial payers do not cover panels >50 genes. Must use 81455. Recommend Z-code registration and MAC pre-check."
    },
    "Solid Tumor – DNA Panel (325 genes)": {
        "risk_level": "High",
        "billing_note": "Panels >300 genes typically require billing with 81455. Ensure strong rationale and clinical documentation to justify extent of profiling."
    },
    "Solid Tumor – DNA + RNA Panel (375 genes)": {
        "risk_level": "High",
        "billing_note": "High complexity assay – may not be reimbursed by all commercial payers. Use 81455 and document clearly why combined profiling was medically necessary."
    },
    "Liquid Biopsy – ctDNA (500 genes)": {
        "risk_level": "Very High",
        "billing_note": "Very few payers reimburse for ctDNA panels >300 genes. Consider alternatives or seek pre-authorization. Billing typically requires 81455."
    },
    "WES – SOPHiA Exome Backbone (19000 genes)": {
        "risk_level": "Very High",
        "billing_note": "Exome sequencing is rarely reimbursed as first-line test. Pairing with carved-out panels may help justify clinical utility and improve ROI."
    },
    "WGS – SOPHiA Genome Backbone (20000+ genes)": {
        "risk_level": "Very High",
        "billing_note": "Whole genome sequencing is high-cost and low reimbursement unless bundled with additional diagnostic or carved-out reportable panels."
    }
}

filter_risk = st.multiselect("Filter panels by risk level:", options=["Low", "Medium", "High", "Very High"])
filtered_panels = [p for p in available_panels if not filter_risk or risk_notes.get(p, {}).get("risk_level") in filter_risk]
if selected_panel not in filtered_panels:
    st.warning("Selected panel does not meet risk filter.")

# --------------------------
# Step 5: Risk & CPT Code Guidance
# --------------------------
st.markdown("## Step 5: Risk and CPT Guidance")
if selected_panel in sophia_panels:
    panel_gene_count = sophia_panels[selected_panel]
else:
    st.error("Selected panel is not recognized. Please check your selection.")
    st.stop()

if selected_panel in risk_notes:
    risk_level = risk_notes[selected_panel]['risk_level']
    badge_color = {
        "Low": "✅",
        "Medium": "🟡",
        "High": "🔴",
        "Very High": "🚨"
    }.get(risk_level, "⚠️")
    st.markdown(f"### {badge_color} **Risk Level: {risk_level}**")
    billing_note = risk_notes[selected_panel]['billing_note']
    st.info(billing_note)
else:
    risk_level = "Not Specified"
    billing_note = "Standard documentation applies."

cpt_mapping = {"<50": "81450", "50-100": "81455", ">100": "81455"}
if panel_gene_count <= 50:
    suggested_cpt = cpt_mapping["<50"]
elif 50 < panel_gene_count <= 100:
    suggested_cpt = cpt_mapping["50-100"]
else:
    suggested_cpt = cpt_mapping[">100"]

st.markdown(f"### CPT Code Recommendation: **{suggested_cpt}**")

# --------------------------
# Step 6: Billing Documentation Guidance
# --------------------------
st.markdown("## Step 6: Billing Documentation")
st.markdown(f"**{selected_panel}** → {billing_note}")

# --------------------------
# Step 7: ROI Simulation for WES/WGS Carve-Outs
# --------------------------
if test_strategy.startswith("Carve-out"):
    st.markdown("## Step 7: ROI Simulation – Carve-Out Modeling")
    st.markdown("Simulate how many carved-out panels per sample are needed to make WES or WGS cost-effective.")

    cost = st.number_input("Total Cost per WES/WGS Test ($):", min_value=500, max_value=3000, value=1200)
    reimbursement_per_panel = st.number_input("Average Reimbursement per Carve-Out Panel ($):", min_value=100, max_value=2000, value=400)
    max_panels = st.slider("Number of Panel Reports per Backbone Test:", min_value=1, max_value=10, value=5)

    break_even_panels = cost / reimbursement_per_panel
    actual_revenue = [n * reimbursement_per_panel for n in range(1, max_panels + 1)]
    profit = [rev - cost for rev in actual_revenue]

    df = pd.DataFrame({
        "# Panels": list(range(1, max_panels + 1)),
        "Revenue ($)": actual_revenue,
        "Profit ($)": profit
    })

    fig, ax = plt.subplots()
    sns.barplot(data=df, x="# Panels", y="Profit ($)", ax=ax, palette="coolwarm")
    ax.axhline(0, color='gray', linestyle='--')
    ax.set_title("Profitability Based on Panel Carve-Outs")
    st.pyplot(fig)

    st.markdown(f"To break even, you need approximately **{break_even_panels:.1f}** panel reports per {test_strategy}.")

# --------------------------
# Step 8: Regional Denial Rates Visualization
# --------------------------
st.markdown("## Step 8: Regional Denial Rates")
st.markdown("Use the interactive map below to educate labs on payer-specific NGS denial risks by region.")

import plotly.express as px

# Sample data – replace with real regional data when available
state_data = {
    "State": ["California", "Texas", "Florida", "New York", "Illinois", "Georgia", "Pennsylvania", "Ohio", "North Carolina", "Michigan"],
    "Denial Rate (%)": [12, 18, 15, 10, 17, 14, 13, 16, 11, 19]
}
df_states = pd.DataFrame(state_data)

fig = px.choropleth(
    df_states,
    locations="State",
    locationmode="USA-states",
    color="Denial Rate (%)",
    color_continuous_scale="Reds",
    scope="usa",
    title="Estimated NGS Denial Rates by State"
)

st.plotly_chart(fig, use_container_width=True)

# --------------------------
# Step 9: Report Download
# --------------------------
report_data = {
    "ZIP Code": zip_code,
    "Test Strategy": test_strategy,
    "Test Type": test_type,
    "Panel": selected_panel,
    "Risk Level": risk_level,
    "CPT Code": suggested_cpt,
    "Billing Note": billing_note,
    "Date": datetime.now().strftime("%Y-%m-%d")
}

# CSV Export
csv_data = pd.DataFrame([report_data])
csv = csv_data.to_csv(index=False).encode('utf-8')
st.download_button("⬇️ Download CSV Report", data=csv, file_name="ngs_report.csv", mime="text/csv")

# PDF Export
pdf_buffer = BytesIO()
c = canvas.Canvas(pdf_buffer, pagesize=letter)
c.drawString(100, 750, "NGS Reimbursement Report")
y = 720
for k, v in report_data.items():
    c.drawString(100, y, f"{k}: {v}")
    y -= 20
c.save()
pdf = pdf_buffer.getvalue()
st.download_button("⬇️ Download PDF Report", data=pdf, file_name="ngs_report.pdf", mime="application/pdf")
