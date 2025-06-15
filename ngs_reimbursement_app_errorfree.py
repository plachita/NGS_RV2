
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO

# App title
st.title("NGS Reimbursement Optimization Tool")

# Step 1: Test Type Selection
st.sidebar.header("Choose Testing Strategy")
testing_mode = st.sidebar.radio("Select Scenario", [
    "Panel-Only Testing",
    "Whole Exome Sequencing (WES)",
    "Whole Genome Sequencing (WGS)"
])

# Step 2: Test Info Section
st.header("Step 1: Test Information")
test_type = st.selectbox("Select Test Type", [
    "Solid Tumor – DNA Panel",
    "Solid Tumor – RNA Panel",
    "Solid Tumor – DNA + RNA Panel",
    "Hematologic – DNA Panel",
    "Hematologic – RNA Panel",
    "Hematologic – DNA + RNA Panel",
    "Liquid Biopsy – ctDNA"
])

gene_count = st.slider("Number of Genes in Panel", 1, 500, 50)
lab_cost = st.number_input("Enter Total Lab Cost per Sample ($)", min_value=0.0, value=350.0)
inpatient_pct = st.slider("% of Inpatient Volume (14-Day Rule Applies)", 0, 100, 30)

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

    # Drill-down by CPT
    st.subheader("Drill Down by CPT Code")
    selected_cpt = st.selectbox("Filter data by CPT code", options=sorted(df['cpt_code'].unique()))
    st.dataframe(df[df['cpt_code'] == selected_cpt])

    # Payer-specific denial filtering
    st.subheader("Filter by Payer")
    if 'payer' in df.columns:
        selected_payer = st.selectbox("Choose payer to view related tests", sorted(df['payer'].dropna().unique()))
        st.dataframe(df[df['payer'] == selected_payer])

    # SNOMED/LOINC mapping with educational tooltips
    st.subheader("SNOMED/LOINC Mapping Preview")
    if 'test_name' in df.columns:
        st.markdown("Use SNOMED for clinical condition encoding and LOINC for lab test identity. These help align with EHRs and increase billing success.")
        mapping_preview = df[['test_name']].drop_duplicates().copy()
        mapping_preview['SNOMED'] = mapping_preview['test_name'].apply(lambda x: "123456" if "myeloid" in x.lower() else "654321")
        mapping_preview['LOINC'] = mapping_preview['test_name'].apply(lambda x: "98765-4" if "fusion" in x.lower() else "54321-0")
        st.dataframe(mapping_preview)

    # Z-Code Education Module
    st.subheader("Z-Code Education")
    st.markdown("Z-codes are unique identifiers assigned by MolDx to molecular diagnostic tests. They are required by CMS and some private payers for reimbursement of LDTs and NGS panels.")
    st.markdown("**Examples:**")
    st.markdown("- ZB123: Myeloid 50-gene panel (DNA only)")
    st.markdown("- ZC456: Fusion panel (RNA-based)")
    st.markdown("- ZD789: Combined DNA + RNA tumor profiling")
    st.markdown("Z-codes must be registered through the DEX™ Diagnostics Exchange and associated with a valid CPT code. Failure to submit a Z-code may result in **automatic claim denial**.")
    st.markdown("For more info: [DEX Z-code registry](https://app.dexzcodes.com/public/search)")

    # Billing Checklist Generator
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
