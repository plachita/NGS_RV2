import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO

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

# App title
st.title("NGS Reimbursement Optimization Tool")

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

default_gene_count = sophia_panels.get(test_type, 50)
gene_count = st.slider("Number of Genes in Panel", 1, 500, default_gene_count)
lab_cost = st.number_input("Enter Total Lab Cost per Sample ($)", min_value=0.0, value=350.0)
inpatient_pct = st.slider("% of Inpatient Volume (14-Day Rule Applies)", 0, 100, 30)

# Step 2: CPT Code Recommendation
st.header("Step 2: CPT Code Recommendation")
if gene_count > 50:
    cpt_code = "81455"
elif gene_count > 5:
    cpt_code = "81450"
else:
    cpt_code = "81445"

if "Liquid Biopsy" in test_type:
    cpt_code = "0326U"  # Placeholder for FDA-cleared ctDNA assays

if "Germline" in test_type:
    if gene_count > 50:
        cpt_code = "81455"
    elif gene_count > 5:
        cpt_code = "81450"
    else:
        cpt_code = "81445"

st.success(f"Suggested CPT Code: {cpt_code}")

# Step 3: Reimbursement Estimator
st.header("Step 3: Reimbursement Estimator")
cpt_base_rates = {"81445": 600, "81450": 750, "81455": 1200, "0326U": 2800}
base_rate = cpt_base_rates.get(cpt_code, 600)

denial_rate = st.slider("Estimated Denial Rate (%)", 0, 100, 15)
estimated_reimbursement = base_rate * (1 - (denial_rate / 100))
profit_margin = estimated_reimbursement - lab_cost

st.info(f"Estimated Reimbursement: ${estimated_reimbursement:,.2f}")
st.info(f"Estimated Profit per Test: ${profit_margin:,.2f}")

# Step 4: WES/WGS Germline Carve-Out Profitability
st.header("Step 4: WES/WGS Germline Carve-Out Calculator")
if testing_mode in ["Whole Exome Sequencing (WES)", "Whole Genome Sequencing (WGS)"]:
    st.markdown("**Note:** Most carve-out strategies using WES/WGS involve *germline hereditary panels* (e.g., cancer, cardiomyopathy). These panels are billed separately but extracted from the exome/genome backbone.")
    backbone_cost = 800 if testing_mode == "Whole Exome Sequencing (WES)" else 1300
    carveout_margin = profit_margin if profit_margin > 0 else 100
    required_panels = backbone_cost / carveout_margin
    st.warning(f"You need at least {required_panels:.1f} germline carve-out panels per {testing_mode} to break even.")

# Step 5: Strategy Recommendation
st.header("Step 5: Recommended Strategy")
if testing_mode == "Panel-Only Testing" and estimated_reimbursement < lab_cost:
    st.error("Warning: Current panel strategy may not be profitable. Consider revising panel content or switching to WES/WGS.")
else:
    st.success("Panel design appears cost-effective under current assumptions.")

if testing_mode in ["Whole Exome Sequencing (WES)", "Whole Genome Sequencing (WGS)"] and profit_margin > 0:
    st.markdown("✅ Based on your cost assumptions, WES/WGS is likely sustainable with germline panel carve-outs.")

# Carve-out logic toggle
toggle_strategy = st.radio("Carve-Out Strategy Source", [
    "Same Genome (multiple CPTs per sample)",
    "Separate Genomes (one CPT per sample)"
])

# Placeholder for uploaded file
uploaded_file = st.file_uploader("Upload CSV of test names and attributes", type="csv")
if uploaded_file:
    df = pd.read_csv(uploaded_file)

    # Denial Risk Bar Chart
    st.header("Step 6: Visualize Denial Risk")
    risk_counts = df['denial_risk'].value_counts()
    avg_reimbursement_by_risk = df.groupby('denial_risk')['estimated_reimbursement'].mean()

    fig, ax = plt.subplots()
    bars = ax.bar(risk_counts.index, risk_counts.values, color=[
        'green' if r == 'Low' else 'orange' if r == 'Medium' else 'red' for r in risk_counts.index
    ])
    ax.set_title("Denial Risk Levels")
    ax.set_xlabel("Risk Category")
    ax.set_ylabel("Number of Tests")

    for bar, risk in zip(bars, risk_counts.index):
        height = bar.get_height()
        avg_reimb = avg_reimbursement_by_risk[risk]
        ax.text(bar.get_x() + bar.get_width() / 2, height + 0.5, f"Avg: ${avg_reimb:,.0f}",
                ha='center', va='bottom', fontsize=9, fontweight='bold')

    st.pyplot(fig)

    buf = BytesIO()
    fig.savefig(buf, format="png")
    st.download_button(
        label="Download Bar Chart as PNG",
        data=buf.getvalue(),
        file_name="denial_risk_chart.png",
        mime="image/png"
    )

    st.subheader("Drill Down by CPT Code")
    selected_cpt = st.selectbox("Filter data by CPT code", options=sorted(df['cpt_code'].unique()))
    st.dataframe(df[df['cpt_code'] == selected_cpt])

    st.subheader("Filter by Payer")
    if 'payer' in df.columns:
        selected_payer = st.selectbox("Choose payer to view related tests", sorted(df['payer'].dropna().unique()))
        st.dataframe(df[df['payer'] == selected_payer])

    st.subheader("SNOMED/LOINC Mapping Preview")
    if 'test_name' in df.columns:
        st.markdown("Use SNOMED for clinical condition encoding and LOINC for lab test identity. These help align with EHRs and increase billing success.")
        mapping_preview = df[['test_name']].drop_duplicates().copy()
        mapping_preview['SNOMED'] = mapping_preview['test_name'].apply(lambda x: "123456" if "myeloid" in x.lower() else "654321")
        mapping_preview['LOINC'] = mapping_preview['test_name'].apply(lambda x: "98765-4" if "fusion" in x.lower() else "54321-0")
        st.dataframe(mapping_preview)

    st.subheader("Z-Code Education")
    st.markdown("Z-codes are unique identifiers assigned by MolDx to molecular diagnostic tests. They are required by CMS and some private payers for reimbursement of LDTs and NGS panels.")
    st.markdown("**Examples:**")
    st.markdown("- ZB123: Myeloid 50-gene panel (DNA only)")
    st.markdown("- ZC456: Fusion panel (RNA-based)")
    st.markdown("- ZD789: Combined DNA + RNA tumor profiling")
    st.markdown("- ZE321: Germline hereditary cancer panel carved from WES")
    st.markdown("Z-codes must be registered through the DEX™ Diagnostics Exchange and associated with a valid CPT code. Failure to submit a Z-code may result in **automatic claim denial**.")
    st.markdown("For more info: [DEX Z-code registry](https://app.dexzcodes.com/public/search)")

    st.subheader("Billing Documentation Checklist")
    st.markdown("Review this checklist before submitting claims:")
    checklist_items = [
        "✅ CPT Code matches test content and platform",
        "✅ Z-code submitted and registered in DEX",
        "✅ LOINC code present for test identity",
        "✅ SNOMED code linked to clinical indication",
        "✅ Physician order includes diagnosis aligned with payer criteria",
        "✅ Inpatient vs. outpatient correctly documented (14-day rule consideration)",
        "✅ Test panel adheres to gene count thresholds (<50 for payers restricting CPT 81455)",
        "✅ Clinical utility documentation available (e.g., NCCN guideline citation)"
    ]
    for item in checklist_items:
        st.write(item)
    st.markdown("You may copy/paste this list or save it for your billing department.")
