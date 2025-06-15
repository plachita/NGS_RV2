import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import seaborn as sns
import requests

# Define Sophia panels and their gene counts
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
    "Germline – Pediatric/Undiagnosed Disease Panel (160 genes)": 160
}

# Payer documentation requirements
payer_docs = {
    "CMS": [
        "Z-Code registration through DEX registry",
        "Clinical indication matching LCD/NCD language",
        "14-day rule compliance",
        "Signed physician order with diagnosis codes",
        "CPT code aligned with service performed"
    ],
    "BCBS": [
        "Medical policy coverage criteria matched",
        "Preauthorization as required",
        "Genetic counseling documentation",
        "ICD-10 justification",
        "Lab credentialing and accreditation info"
    ],
    "UnitedHealthcare": [
        "Clinical Utility documentation",
        "Pathologist-reviewed report copy",
        "Z-Code or internal payer pre-review ID",
        "Reflex testing logic outlined",
        "CPT accuracy validation"
    ]
}

# MAC region-specific CPT enforcement (stubbed for future expansion)
mac_policy_cpt = {
    "Palmetto (Southeast)": {"max_genes": 50, "required_code": "81450"},
    "Noridian (West)": {"max_genes": 100, "required_code": "81455"},
    "NGS (Northeast)": {"max_genes": 50, "required_code": "81450"},
    "Default MAC": {"max_genes": 100, "required_code": "81455"}
}

# Function to infer MAC from ZIP code

def infer_mac_region(zip_code):
    zip_code = str(zip_code)
    if zip_code.startswith("9"):
        return "Noridian (West)"
    elif zip_code.startswith("7"):
        return "Palmetto (Southeast)"
    elif zip_code.startswith("1"):
        return "NGS (Northeast)"
    else:
        return "Default MAC"

# App title
st.title("NGS Reimbursement Optimization Tool")

# Step 0: Optional Zip Entry
zip_input = st.sidebar.text_input("Enter ZIP Code (optional for MAC region detection)")
if zip_input:
    inferred_mac = infer_mac_region(zip_input)
    st.sidebar.markdown(f"**MAC Region:** {inferred_mac}")
else:
    inferred_mac = "Default MAC"

# Step 1: Test Type Selection
st.sidebar.header("Choose Testing Strategy")
testing_mode = st.sidebar.radio("Select Scenario", [
    "Panel-Only Testing",
    "Whole Exome Sequencing (WES)",
    "Whole Genome Sequencing (WGS)"
])

# Step 1: Test Info Section
st.header("Step 1: Test Information")
test_type = st.selectbox("Select Test Type", list(sophia_panels.keys()))

# Optional: allow multi-panel comparison
compare_panels = st.checkbox("Compare Multiple Panels")
selected_panels = [test_type]
if compare_panels:
    selected_panels = st.multiselect("Select Panels to Compare", list(sophia_panels.keys()), default=[test_type])

payer_policy = st.selectbox("Select Payer Policy", ["CMS", "BCBS", "UnitedHealthcare"])

# Logic table for payer-specific thresholds
payer_thresholds = {
    "CMS": 50,
    "BCBS": 50,
    "UnitedHealthcare": 50
}

risk_levels = []
reimbursement_values = []
roi_values = []

# Step 2-3 logic is computed per panel in this loop
for panel in selected_panels:
    default_gene_count = sophia_panels.get(panel, 50)
    gene_count = default_gene_count
    if not compare_panels:
        gene_count = st.slider("Number of Genes in Panel", 1, 500, default_gene_count)

    # Determine CPT Code
    if "Liquid Biopsy" in panel:
        cpt_code = "0326U"
    elif gene_count > 50:
        cpt_code = "81455"
    elif gene_count > 5:
        cpt_code = "81450"
    else:
        cpt_code = "81445"

    # Base Rates
    cpt_base_rates = {"81445": 600, "81450": 750, "81455": 1200, "0326U": 2800}
    base_rate = cpt_base_rates.get(cpt_code, 600)

    denial_rate = 15
    estimated_reimbursement = base_rate * (1 - (denial_rate / 100))
    reimbursement_values.append(estimated_reimbursement)

    # Denial Risk
    if gene_count > payer_thresholds[payer_policy]:
        risk = "High"
    elif gene_count > 100:
        risk = "Medium"
    else:
        risk = "Low"
    risk_levels.append(risk)

    # ROI Estimation (e.g., 250 cost)
    lab_cost = 250
    roi = round((estimated_reimbursement - lab_cost) / lab_cost, 2)
    roi_values.append(roi)

# Step 6: Enhanced Risk Visualization
st.header("Step 6: Denial Risk & ROI")
fig, ax = plt.subplots()
colors = ["green" if r == "Low" else "orange" if r == "Medium" else "red" for r in risk_levels]
bars = ax.bar(selected_panels, reimbursement_values, color=colors)
ax.set_title("Estimated Reimbursement and Risk")
ax.set_ylabel("$ Reimbursement")
ax.set_xticklabels(selected_panels, rotation=45, ha="right")

# Annotate bars
for bar, risk, reimb, roi in zip(bars, risk_levels, reimbursement_values, roi_values):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 50,
            f"{risk} Risk\n${reimb:,.0f}\nROI: {roi}", ha='center', fontsize=8, fontweight='bold')

st.pyplot(fig)

# Tooltip education
if st.checkbox("Explain Risk Levels"):
    st.markdown("**Risk Level Explanation:**")
    st.markdown("- **Low Risk**: Gene count ≤ 50 (aligned with most payer thresholds)")
    st.markdown("- **Medium Risk**: Gene count 51-100 (coverage varies)")
    st.markdown("- **High Risk**: Gene count > 100 or misaligned with payer policy")

# Step 7: Payer Documentation Requirements
st.header("Step 7: Billing Documentation Guidance")
st.subheader(f"Required Documentation for {payer_policy}:")
for doc in payer_docs[payer_policy]:
    st.markdown(f"- {doc}")

# Step 8: MAC-Specific CPT Logic Check
st.header("Step 8: MAC-Region CPT Recommendations")
mac_rules = mac_policy_cpt.get(inferred_mac, {})
mac_max = mac_rules.get("max_genes", 100)
mac_required_code = mac_rules.get("required_code", "81455")
st.markdown(f"**MAC Policy for {inferred_mac}:**")
st.markdown(f"- Gene Limit: {mac_max} genes")
st.markdown(f"- Preferred CPT Code: {mac_required_code}")

if gene_count > mac_max:
    st.warning(f"This panel exceeds the MAC gene limit. Consider splitting or downcoding cautiously.")

# Future Step: LCD/NCD links and integration
if st.checkbox("Show LCD/NCD Reference (Coming Soon)"):
    st.markdown("[Palmetto LCD L38764](https://www.cms.gov/medicare-coverage-database/view/lcd.aspx?lcdid=38764)")
