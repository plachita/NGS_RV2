import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import json
from typing import Dict, Any, List
import warnings
warnings.filterwarnings('ignore')

# Page configuration
st.set_page_config(
    page_title="NGS Reimbursement Intelligence",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="🧬"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1f77b4, #17becf);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #1f77b4;
        margin: 0.5rem 0;
    }
    .risk-low { color: #28a745; }
    .risk-medium { color: #ffc107; }
    .risk-high { color: #dc3545; }
    .sidebar-info {
        background: #e9ecef;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
def initialize_session_state():
    defaults = {
        'saved_sessions': {},
        'comparison_data': [],
        'benchmark_data': None,
        'current_profile': None
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

initialize_session_state()

# Enhanced risk calculation with more factors
def calculate_comprehensive_risk(backbone: str, positioning: str, region: str, 
                               reporting: str, specialty: str, volume: int) -> Dict[str, float]:
    """Enhanced risk calculation with multiple factors"""
    
    # Base risk factors
    backbone_risk = {"Panel": 0.8, "Exome": 1.0, "Genome": 1.2}
    positioning_risk = {"First-line": 1.1, "Reflex": 0.9, "Confirmatory": 0.7}
    region_risk = {"National": 1.0, "Northeast": 0.9, "South": 1.2, "Midwest": 1.0, "West": 1.1}
    reporting_risk = {"Full Report": 1.0, "Carve-out Panels": 0.9}
    specialty_risk = {"Oncology": 0.8, "Cardiology": 1.0, "Neurology": 1.1, "Rare Disease": 1.3, "Prenatal": 0.9}
    
    # Volume-based risk (higher volume = lower risk due to established relationships)
    volume_risk = max(0.7, 1.2 - (volume / 5000))
    
    base_score = (backbone_risk.get(backbone, 1.0) * 
                  positioning_risk.get(positioning, 1.0) * 
                  region_risk.get(region, 1.0) * 
                  reporting_risk.get(reporting, 1.0) * 
                  specialty_risk.get(specialty, 1.0) * 
                  volume_risk)
    
    # Calculate component risks
    components = {
        'Prior Authorization Risk': min(base_score * 0.8, 1.0),
        'Denial Risk': min(base_score * 0.6, 1.0),
        'Appeal Success Rate': max(0.3, 1.0 - base_score * 0.4),
        'Time to Payment Risk': min(base_score * 0.7, 1.0)
    }
    
    return {'overall': base_score, **components}

# Enhanced financial calculations
def calculate_enhanced_financials(cost_per_sample: float, reimbursement: float, 
                                volume: int, denial_rate: float) -> Dict[str, float]:
    """Calculate comprehensive financial metrics"""
    
    gross_profit = reimbursement - cost_per_sample
    effective_reimbursement = reimbursement * (1 - denial_rate)
    net_profit = effective_reimbursement - cost_per_sample
    
    annual_gross_revenue = reimbursement * volume
    annual_net_revenue = effective_reimbursement * volume
    annual_costs = cost_per_sample * volume
    annual_net_profit = net_profit * volume
    
    roi = (net_profit / cost_per_sample * 100) if cost_per_sample > 0 else 0
    margin = (net_profit / effective_reimbursement * 100) if effective_reimbursement > 0 else 0
    
    return {
        'gross_profit': gross_profit,
        'net_profit': net_profit,
        'effective_reimbursement': effective_reimbursement,
        'annual_gross_revenue': annual_gross_revenue,
        'annual_net_revenue': annual_net_revenue,
        'annual_costs': annual_costs,
        'annual_net_profit': annual_net_profit,
        'roi': roi,
        'margin': margin,
        'denial_impact': (gross_profit - net_profit) * volume
    }

# Sidebar for quick navigation and tips
with st.sidebar:
    st.markdown("### 🧬 NGS Intelligence Hub")
    st.markdown("Navigate through different sections to analyze your NGS testing economics.")
    
    st.markdown("### 💡 Quick Tips")
    with st.expander("Optimize Your Testing"):
        st.markdown("""
        - **Higher volumes** typically reduce denial risk
        - **Panel tests** have lower denial rates than WES/WGS
        - **Reflex testing** often has better reimbursement
        - **Prior authorization** can reduce denials by 30-50%
        """)
    
    st.markdown("### 📊 Benchmarks")
    if st.button("Load Industry Benchmarks"):
        st.session_state.benchmark_data = {
            'panel_cost': 650, 'exome_cost': 850, 'genome_cost': 1200,
            'avg_reimbursement': 1050, 'avg_denial_rate': 0.15
        }
        st.success("Benchmarks loaded!")

# Main header
st.markdown('<div class="main-header"><h1>🧬 NGS Reimbursement Intelligence Platform</h1><p>Comprehensive financial analysis for Next-Generation Sequencing operations</p></div>', unsafe_allow_html=True)

# Enhanced tabs
tabs = st.tabs([
    "🏥 Lab Profile", 
    "💰 Financial Analysis", 
    "⚠️ Risk Assessment", 
    "📈 Projections & Scenarios", 
    "🔄 Workflow Comparison", 
    "📊 Benchmarking",
    "💾 Export & Reports", 
    "📖 Resources"
])

# Enhanced Lab Profile Tab
with tabs[0]:
    st.header("Laboratory Profile Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Test Configuration")
        backbone = st.selectbox(
            "Test Backbone", 
            ["Panel", "Exome", "Genome"],
            help="Select the primary sequencing approach"
        )
        
        reporting = st.radio(
            "Reporting Strategy", 
            ["Full Report", "Carve-out Panels"],
            help="Full genomic analysis or targeted subset reporting"
        )
        
        positioning = st.selectbox(
            "Test Positioning", 
            ["First-line", "Reflex", "Confirmatory"],
            help="When the test is ordered in the diagnostic workflow"
        )
        
        specialty = st.selectbox(
            "Medical Specialty",
            ["Oncology", "Cardiology", "Neurology", "Rare Disease", "Prenatal"],
            help="Primary medical specialty using the test"
        )
    
    with col2:
        st.subheader("Operational Parameters")
        region = st.selectbox(
            "Primary Region", 
            ["National", "Northeast", "South", "Midwest", "West"],
            help="Geographic region affects payer mix and policies"
        )
        
        annual_volume = st.number_input(
            "Annual Test Volume", 
            min_value=1, 
            value=1000,
            help="Expected annual number of tests"
        )
        
        batch_size = st.number_input(
            "Batch Size", 
            min_value=1, 
            value=20,
            help="Samples processed per sequencing run"
        )
        
        prior_auth_rate = st.slider(
            "Prior Authorization Rate (%)",
            0, 100, 60,
            help="Percentage of cases with prior authorization"
        ) / 100

    st.subheader("Cost Structure")
    col3, col4 = st.columns(2)
    
    with col3:
        cost_per_sample = st.number_input(
            "Total Cost per Sample ($)", 
            min_value=0.0, 
            value=728.00,
            help="All-in cost including reagents, labor, overhead"
        )
        
        lab_overhead = st.number_input(
            "Monthly Lab Overhead ($)",
            min_value=0.0,
            value=25000.0,
            help="Fixed monthly costs (rent, utilities, base staff)"
        )
    
    with col4:
        reimbursement = st.number_input(
            "Expected Reimbursement ($)", 
            min_value=0.0, 
            value=1000.00,
            help="Average expected payer reimbursement"
        )
        
        bad_debt_rate = st.slider(
            "Bad Debt Rate (%)",
            0, 30, 5,
            help="Percentage of uncollectable receivables"
        ) / 100

# Calculate enhanced metrics
risk_metrics = calculate_comprehensive_risk(backbone, positioning, region, reporting, specialty, annual_volume)
base_denial_rate = risk_metrics['overall'] * 0.15  # Base denial rate
adjusted_denial_rate = base_denial_rate * (1 - prior_auth_rate * 0.4)  # Prior auth reduces denials
total_loss_rate = adjusted_denial_rate + bad_debt_rate

financials = calculate_enhanced_financials(cost_per_sample, reimbursement, annual_volume, total_loss_rate)

# Enhanced Financial Analysis Tab
with tabs[1]:
    st.header("Comprehensive Financial Analysis")
    
    # Key metrics dashboard
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Net Profit per Test",
            f"${financials['net_profit']:.2f}",
            delta=f"${financials['net_profit'] - financials['gross_profit']:.2f}"
        )
    
    with col2:
        st.metric(
            "Effective ROI",
            f"{financials['roi']:.1f}%",
            delta=f"{financials['margin']:.1f}% margin"
        )
    
    with col3:
        st.metric(
            "Annual Net Revenue",
            f"${financials['annual_net_revenue']:,.0f}",
            delta=f"-${financials['denial_impact']:,.0f} lost to denials"
        )
    
    with col4:
        collection_rate = (1 - total_loss_rate) * 100
        st.metric(
            "Collection Rate",
            f"{collection_rate:.1f}%",
            delta=f"{adjusted_denial_rate*100:.1f}% denial rate"
        )
    
    # Detailed financial breakdown
    st.subheader("Revenue Waterfall Analysis")
    
    waterfall_data = pd.DataFrame({
        'Category': ['Gross Revenue', 'Denials', 'Bad Debt', 'Net Revenue', 'Costs', 'Net Profit'],
        'Amount': [
            financials['annual_gross_revenue'],
            -financials['annual_gross_revenue'] * adjusted_denial_rate,
            -financials['annual_gross_revenue'] * bad_debt_rate,
            financials['annual_net_revenue'],
            -financials['annual_costs'],
            financials['annual_net_profit']
        ]
    })
    
    fig_waterfall = go.Figure(go.Waterfall(
        name="Revenue Flow",
        orientation="v",
        measure=["absolute", "relative", "relative", "total", "relative", "total"],
        x=waterfall_data['Category'],
        y=waterfall_data['Amount'],
        connector={"line": {"color": "rgb(63, 63, 63)"}},
    ))
    
    fig_waterfall.update_layout(
        title="Annual Revenue Waterfall ($)",
        showlegend=False,
        height=500
    )
    st.plotly_chart(fig_waterfall, use_container_width=True)
    
    # Monthly cashflow projection
    st.subheader("Monthly Cash Flow Projection")
    months = pd.date_range(start=datetime.now(), periods=12, freq='M')
    monthly_volume = annual_volume / 12
    monthly_revenue = financials['annual_net_revenue'] / 12
    monthly_costs = financials['annual_costs'] / 12 + lab_overhead
    monthly_profit = monthly_revenue - monthly_costs
    
    cashflow_df = pd.DataFrame({
        'Month': months,
        'Revenue': [monthly_revenue] * 12,
        'Costs': [monthly_costs] * 12,
        'Profit': [monthly_profit] * 12,
        'Cumulative Profit': np.cumsum([monthly_profit] * 12)
    })
    
    fig_cashflow = go.Figure()
    fig_cashflow.add_trace(go.Scatter(x=cashflow_df['Month'], y=cashflow_df['Revenue'], name='Monthly Revenue', fill='tonexty'))
    fig_cashflow.add_trace(go.Scatter(x=cashflow_df['Month'], y=cashflow_df['Costs'], name='Monthly Costs', fill='tozeroy'))
    fig_cashflow.add_trace(go.Scatter(x=cashflow_df['Month'], y=cashflow_df['Cumulative Profit'], name='Cumulative Profit', yaxis='y2'))
    
    fig_cashflow.update_layout(
        title="12-Month Cash Flow Projection",
        xaxis_title="Month",
        yaxis_title="Monthly Amount ($)",
        yaxis2=dict(title="Cumulative Profit ($)", overlaying='y', side='right'),
        hovermode='x unified'
    )
    st.plotly_chart(fig_cashflow, use_container_width=True)

# Enhanced Risk Assessment Tab
with tabs[2]:
    st.header("Multi-Factor Risk Assessment")
    
    # Risk dashboard
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Risk Components Analysis")
        
        risk_df = pd.DataFrame({
            'Risk Factor': list(risk_metrics.keys())[1:],  # Exclude 'overall'
            'Score': [risk_metrics[key] for key in list(risk_metrics.keys())[1:]],
            'Impact': ['High', 'High', 'Medium', 'Medium']
        })
        
        fig_risk = px.bar(
            risk_df, 
            x='Score', 
            y='Risk Factor',
            color='Impact',
            orientation='h',
            title="Individual Risk Component Scores"
        )
        fig_risk.update_layout(height=400)
        st.plotly_chart(fig_risk, use_container_width=True)
    
    with col2:
        st.subheader("Overall Risk Level")
        
        risk_level = "Low" if risk_metrics['overall'] < 1.0 else "Medium" if risk_metrics['overall'] < 1.3 else "High"
        risk_color = "risk-low" if risk_level == "Low" else "risk-medium" if risk_level == "Medium" else "risk-high"
        
        st.markdown(f"<div class='{risk_color}'><h2>{risk_level} Risk</h2><h3>Score: {risk_metrics['overall']:.2f}</h3></div>", unsafe_allow_html=True)
        
        st.progress(min(risk_metrics['overall'] / 2, 1.0))
        
        # Risk mitigation suggestions
        st.subheader("Risk Mitigation")
        if risk_metrics['overall'] > 1.2:
            st.warning("Consider implementing prior authorization workflow")
        if adjusted_denial_rate > 0.2:
            st.error("High denial rate - review test ordering criteria")
        if bad_debt_rate > 0.1:
            st.warning("Consider improving patient financial counseling")

# Enhanced Projections & Scenarios Tab
with tabs[3]:
    st.header("Projections & Scenario Analysis")
    
    st.subheader("Volume Sensitivity Analysis")
    
    # Scenario parameters
    col1, col2 = st.columns(2)
    with col1:
        scenario_volumes = st.multiselect(
            "Test Volumes to Analyze",
            [500, 1000, 2000, 5000, 10000],
            default=[annual_volume, annual_volume*2]
        )
    
    with col2:
        price_scenarios = st.multiselect(
            "Reimbursement Scenarios ($)",
            [800, 900, 1000, 1100, 1200],
            default=[reimbursement]
        )
    
    # Generate scenario matrix
    if scenario_volumes and price_scenarios:
        scenario_data = []
        for vol in scenario_volumes:
            for price in price_scenarios:
                scenario_risk = calculate_comprehensive_risk(backbone, positioning, region, reporting, specialty, vol)
                scenario_denial = scenario_risk['overall'] * 0.15 * (1 - prior_auth_rate * 0.4)
                scenario_loss_rate = scenario_denial + bad_debt_rate
                scenario_financials = calculate_enhanced_financials(cost_per_sample, price, vol, scenario_loss_rate)
                
                scenario_data.append({
                    'Volume': vol,
                    'Price': price,
                    'Annual Profit': scenario_financials['annual_net_profit'],
                    'ROI': scenario_financials['roi'],
                    'Risk Score': scenario_risk['overall']
                })
        
        scenario_df = pd.DataFrame(scenario_data)
        
        # Heatmap of profitability
        pivot_profit = scenario_df.pivot(index='Price', columns='Volume', values='Annual Profit')
        
        fig_heatmap = px.imshow(
            pivot_profit,
            labels=dict(x="Annual Volume", y="Reimbursement ($)", color="Annual Profit ($)"),
            title="Profitability Heatmap by Volume and Price"
        )
        st.plotly_chart(fig_heatmap, use_container_width=True)
        
        # Breakeven analysis
        st.subheader("Break-Even Analysis")
        breakeven_volume = financials['annual_costs'] / financials['net_profit'] if financials['net_profit'] > 0 else np.inf
        
        if breakeven_volume != np.inf:
            st.success(f"Break-even volume: {breakeven_volume:,.0f} tests annually")
        else:
            st.error("Current pricing does not support profitability")
        
        # Monte Carlo simulation
        st.subheader("Monte Carlo Risk Simulation")
        if st.button("Run Simulation"):
            n_simulations = 1000
            results = []
            
            for _ in range(n_simulations):
                # Random variations in key parameters
                sim_volume = np.random.normal(annual_volume, annual_volume * 0.1)
                sim_cost = np.random.normal(cost_per_sample, cost_per_sample * 0.05)
                sim_reimbursement = np.random.normal(reimbursement, reimbursement * 0.1)
                sim_denial_rate = np.random.beta(2, 8) * 0.3  # Skewed towards lower denial rates
                
                sim_financials = calculate_enhanced_financials(sim_cost, sim_reimbursement, int(sim_volume), sim_denial_rate)
                results.append(sim_financials['annual_net_profit'])
            
            results = np.array(results)
            
            fig_mc = go.Figure()
            fig_mc.add_trace(go.Histogram(x=results, nbinsx=50, name="Profit Distribution"))
            fig_mc.add_vline(x=np.percentile(results, 5), line_dash="dash", annotation_text="5th Percentile")
            fig_mc.add_vline(x=np.percentile(results, 95), line_dash="dash", annotation_text="95th Percentile")
            fig_mc.update_layout(title="Monte Carlo Simulation: Annual Profit Distribution")
            st.plotly_chart(fig_mc, use_container_width=True)
            
            st.info(f"90% confidence interval: ${np.percentile(results, 5):,.0f} to ${np.percentile(results, 95):,.0f}")

# Enhanced Workflow Comparison Tab
with tabs[4]:
    st.header("Comprehensive Workflow Comparison")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Current Workflow")
        current_cost = st.number_input("Current Cost per Sample ($)", min_value=0.0, value=950.0)
        current_tat = st.number_input("Current TAT (days)", min_value=0.0, value=10.0)
        current_software_cost = st.number_input("Annual Software Cost ($)", min_value=0.0, value=20000.0)
        current_fte = st.number_input("FTE Required", min_value=0.0, value=2.0)
        current_error_rate = st.slider("Error Rate (%)", 0.0, 10.0, 2.0) / 100
        current_capacity = st.number_input("Max Annual Capacity", min_value=1, value=2000)
    
    with col2:
        st.subheader("SOPHiA DDM Workflow")
        sophia_cost = st.number_input("SOPHiA Cost per Sample ($)", min_value=0.0, value=750.0)
        sophia_tat = st.number_input("SOPHiA TAT (days)", min_value=0.0, value=5.0)
        sophia_software_cost = st.number_input("SOPHiA Annual Cost ($)", min_value=0.0, value=50000.0)
        sophia_fte = st.number_input("SOPHiA FTE Required", min_value=0.0, value=1.5)
        sophia_error_rate = st.slider("SOPHiA Error Rate (%)", 0.0, 10.0, 0.5) / 100
        sophia_capacity = st.number_input("SOPHiA Max Capacity", min_value=1, value=5000)
    
    # Comprehensive comparison
    st.subheader("Detailed Comparison Analysis")
    
    comparison_metrics = {
        'Metric': [
            'Cost per Sample', 'Annual Software Cost', 'FTE Required', 
            'Turnaround Time', 'Error Rate', 'Max Capacity',
            'Annual Cost (1000 samples)', 'Cost per FTE', 'Quality Score'
        ],
        'Current Workflow': [
            f"${current_cost:.2f}",
            f"${current_software_cost:,.0f}",
            f"{current_fte:.1f}",
            f"{current_tat:.1f} days",
            f"{current_error_rate*100:.1f}%",
            f"{current_capacity:,}",
            f"${(current_cost * 1000 + current_software_cost):,.0f}",
            f"${current_cost * 1000 / current_fte if current_fte > 0 else 0:,.0f}",
            f"{(1-current_error_rate)*100:.1f}%"
        ],
        'SOPHiA Workflow': [
            f"${sophia_cost:.2f}",
            f"${sophia_software_cost:,.0f}",
            f"{sophia_fte:.1f}",
            f"{sophia_tat:.1f} days",
            f"{sophia_error_rate*100:.1f}%",
            f"{sophia_capacity:,}",
            f"${(sophia_cost * 1000 + sophia_software_cost):,.0f}",
            f"${sophia_cost * 1000 / sophia_fte if sophia_fte > 0 else 0:,.0f}",
            f"{(1-sophia_error_rate)*100:.1f}%"
        ]
    }
    
    comparison_df = pd.DataFrame(comparison_metrics)
    st.dataframe(comparison_df, use_container_width=True)
    
    # ROI Analysis over time
    st.subheader("5-Year ROI Projection")
    years = range(1, 6)
    volumes = [min(annual_volume * (1.1 ** (year-1)), min(current_capacity, sophia_capacity)) for year in years]
    
    current_costs = [(current_cost * vol + current_software_cost + current_fte * 100000) for vol in volumes]
    sophia_costs = [(sophia_cost * vol + sophia_software_cost + sophia_fte * 100000) for vol in volumes]
    cumulative_savings = np.cumsum([c - s for c, s in zip(current_costs, sophia_costs)])
    
    fig_roi = go.Figure()
    fig_roi.add_trace(go.Scatter(x=list(years), y=current_costs, name='Current Workflow', line=dict(color='red')))
    fig_roi.add_trace(go.Scatter(x=list(years), y=sophia_costs, name='SOPHiA Workflow', line=dict(color='blue')))
    fig_roi.add_trace(go.Scatter(x=list(years), y=cumulative_savings, name='Cumulative Savings', yaxis='y2', line=dict(color='green')))
    
    fig_roi.update_layout(
        title="5-Year Cost Comparison and Savings",
        xaxis_title="Year",
        yaxis_title="Annual Cost ($)",
        yaxis2=dict(title="Cumulative Savings ($)", overlaying='y', side='right'),
        hovermode='x unified'
    )
    st.plotly_chart(fig_roi, use_container_width=True)

# New Benchmarking Tab
with tabs[5]:
    st.header("Industry Benchmarking")
    
    if st.session_state.benchmark_data:
        st.subheader("Your Performance vs Industry Averages")
        
        # Benchmarking comparison
        benchmark_comparison = {
            'Metric': ['Cost per Sample', 'Average Reimbursement', 'Estimated Denial Rate'],
            'Your Lab': [f"${cost_per_sample:.2f}", f"${reimbursement:.2f}", f"{adjusted_denial_rate*100:.1f}%"],
            'Industry Average': [
                f"${st.session_state.benchmark_data[backbone.lower() + '_cost']:.2f}",
                f"${st.session_state.benchmark_data['avg_reimbursement']:.2f}",
                f"{st.session_state.benchmark_data['avg_denial_rate']*100:.1f}%"
            ],
            'Performance': [
                "✅ Better" if cost_per_sample < st.session_state.benchmark_data[backbone.lower() + '_cost'] else "⚠️ Higher",
                "✅ Better" if reimbursement > st.session_state.benchmark_data['avg_reimbursement'] else "⚠️ Lower",
                "✅ Better" if adjusted_denial_rate < st.session_state.benchmark_data['avg_denial_rate'] else "⚠️ Higher"
            ]
        }
        
        benchmark_df = pd.DataFrame(benchmark_comparison)
        st.dataframe(benchmark_df, use_container_width=True)
        
        # Percentile analysis
        st.subheader("Performance Percentile Estimation")
        cost_percentile = 100 - (cost_per_sample / st.session_state.benchmark_data[backbone.lower() + '_cost']) * 50
        reimbursement_percentile = (reimbursement / st.session_state.benchmark_data['avg_reimbursement']) * 50
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Cost Efficiency Percentile", f"{max(0, min(100, cost_percentile)):.0f}%")
        with col2:
            st.metric("Reimbursement Percentile", f"{max(0, min(100, reimbursement_percentile)):.0f}%")
    
    else:
        st.info("Load industry benchmarks from the sidebar to see comparisons.")

# Enhanced Export & Reports Tab
with tabs[6]:
    st.header("Export & Report Generation")
    
    # Session management
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Session Management")
        session_name = st.text_input("Session Name", value=f"NGS_Analysis_{datetime.now().strftime('%Y%m%d_%H%M')}")
        
        if st.button("💾 Save Current Session"):
            session_data = {
                'timestamp': datetime.now().isoformat(),
                'lab_profile': {
                    'backbone': backbone, 'reporting': reporting, 'positioning': positioning,
                    'specialty': specialty, 'region': region, 'annual_volume': annual_volume,
                    'batch_size': batch_size, 'prior_auth_rate': prior_auth_rate
                },
                'financials': financials,
                'risk_metrics': risk_metrics,
                'costs': {'cost_per_sample': cost_per_sample, 'lab_overhead': lab_overhead},
                'reimbursement': reimbursement,
                'rates': {'denial_rate': adjusted_denial_rate, 'bad_debt_rate': bad_debt_rate}
            }
            st.session_state['saved_sessions'][session_name] = session_data
            st.success(f"Session '{session_name}' saved successfully!")
    
    with col2:
        st.subheader("Load Saved Session")
        if st.session_state['saved_sessions']:
            selected_session = st.selectbox("Select Session:", list(st.session_state['saved_sessions'].keys()))
            
            if st.button("📂 Load Session"):
                loaded_data = st.session_state['saved_sessions'][selected_session]
                st.success(f"Session '{selected_session}' loaded!")
                st.json(loaded_data['lab_profile'])
            
            if st.button("🗑️ Delete Session"):
                del st.session_state['saved_sessions'][selected_session]
                st.success("Session deleted!")
                st.rerun()
        else:
            st.info("No saved sessions available.")
    
    # Report generation
    st.subheader("📊 Generate Comprehensive Report")
    
    report_options = st.multiselect(
        "Select Report Sections:",
        ["Executive Summary", "Financial Analysis", "Risk Assessment", "Projections", "Benchmarking", "Recommendations"],
        default=["Executive Summary", "Financial Analysis", "Risk Assessment"]
    )
    
    col3, col4 = st.columns(2)
    
    with col3:
        if st.button("📄 Generate PDF Report"):
            st.info("PDF generation would be implemented with reportlab or similar library")
    
    with col4:
        # JSON Export
        comprehensive_report = {
            'report_metadata': {
                'generated_date': datetime.now().isoformat(),
                'lab_name': session_name,
                'report_version': '2.0'
            },
            'lab_profile': {
                'test_configuration': {
                    'backbone': backbone,
                    'reporting': reporting,
                    'positioning': positioning,
                    'specialty': specialty,
                    'region': region
                },
                'operational_parameters': {
                    'annual_volume': annual_volume,
                    'batch_size': batch_size,
                    'prior_auth_rate': prior_auth_rate,
                    'bad_debt_rate': bad_debt_rate
                },
                'cost_structure': {
                    'cost_per_sample': cost_per_sample,
                    'monthly_overhead': lab_overhead,
                    'expected_reimbursement': reimbursement
                }
            },
            'financial_analysis': financials,
            'risk_assessment': risk_metrics,
            'key_insights': {
                'breakeven_volume': financials['annual_costs'] / financials['net_profit'] if financials['net_profit'] > 0 else None,
                'risk_level': "Low" if risk_metrics['overall'] < 1.0 else "Medium" if risk_metrics['overall'] < 1.3 else "High",
                'collection_rate': (1 - total_loss_rate) * 100,
                'profitability_status': "Profitable" if financials['net_profit'] > 0 else "Loss-making"
            }
        }
        
        json_report = json.dumps(comprehensive_report, indent=2, default=str)
        
        st.download_button(
            label="📥 Download JSON Report",
            data=json_report,
            file_name=f"NGS_Analysis_{session_name}_{datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json"
        )
    
    # Executive Summary
    if "Executive Summary" in report_options:
        st.subheader("📋 Executive Summary")
        
        summary_col1, summary_col2 = st.columns(2)
        
        with summary_col1:
            st.markdown("### Key Financial Metrics")
            st.write(f"• **Annual Net Profit:** ${financials['annual_net_profit']:,.0f}")
            st.write(f"• **Net Profit per Test:** ${financials['net_profit']:.2f}")
            st.write(f"• **Effective ROI:** {financials['roi']:.1f}%")
            st.write(f"• **Collection Rate:** {(1-total_loss_rate)*100:.1f}%")
        
        with summary_col2:
            st.markdown("### Risk Profile")
            risk_level = "Low" if risk_metrics['overall'] < 1.0 else "Medium" if risk_metrics['overall'] < 1.3 else "High"
            st.write(f"• **Overall Risk Level:** {risk_level}")
            st.write(f"• **Risk Score:** {risk_metrics['overall']:.2f}")
            st.write(f"• **Estimated Denial Rate:** {adjusted_denial_rate*100:.1f}%")
            st.write(f"• **Prior Auth Coverage:** {prior_auth_rate*100:.0f}%")
        
        # Recommendations
        st.markdown("### Strategic Recommendations")
        recommendations = []
        
        if financials['roi'] < 20:
            recommendations.append("Consider optimizing cost structure or negotiating better reimbursement rates")
        if adjusted_denial_rate > 0.15:
            recommendations.append("Implement comprehensive prior authorization program")
        if risk_metrics['overall'] > 1.2:
            recommendations.append("Review test ordering criteria and improve clinical documentation")
        if bad_debt_rate > 0.08:
            recommendations.append("Enhance patient financial counseling and payment processes")
        if annual_volume < 1000:
            recommendations.append("Focus on volume growth to achieve economies of scale")
        
        if not recommendations:
            recommendations.append("Current operations appear well-optimized. Monitor key metrics regularly.")
        
        for i, rec in enumerate(recommendations, 1):
            st.write(f"{i}. {rec}")

# Resources Tab
with tabs[7]:
    st.header("📖 Resources & Documentation")
    
    # Enhanced glossary with search
    st.subheader("🔍 Interactive Glossary")
    
    glossary_terms = {
        "Test Backbone": "The core sequencing methodology - Panel (targeted genes), Exome (protein-coding regions), or Genome (whole genome)",
        "Carve-out Panels": "Strategy of running comprehensive sequencing but reporting only clinically relevant subsets",
        "Reflex Testing": "Secondary testing triggered by initial results, often has better reimbursement due to medical necessity",
        "Prior Authorization": "Pre-approval from payers before testing, significantly reduces denial rates",
        "ROI (Return on Investment)": "Percentage return calculated as (Net Profit / Cost) × 100",
        "Risk Score": "Proprietary metric combining test type, positioning, regional factors, and volume to predict denial likelihood",
        "Denial Rate": "Percentage of claims rejected by payers, varies by test type and clinical context",
        "Bad Debt Rate": "Percentage of patient responsibility amounts that remain uncollectable",
        "Collection Rate": "Percentage of billed amounts successfully collected after denials and bad debt",
        "Effective Reimbursement": "Actual average payment received after accounting for denials and bad debt",
        "Break-even Volume": "Number of tests needed annually to cover all fixed and variable costs",
        "Batch Size": "Number of samples processed together, affects per-sample costs through economies of scale",
        "Turnaround Time (TAT)": "Time from sample receipt to report delivery, affects competitive positioning",
        "Monte Carlo Simulation": "Statistical method using random sampling to model probability distributions of outcomes",
        "Waterfall Analysis": "Visual representation showing how gross revenue flows to net profit through various deductions"
    }
    
    search_term = st.text_input("Search glossary terms:", placeholder="Type to search...")
    
    if search_term:
        filtered_terms = {k: v for k, v in glossary_terms.items() if search_term.lower() in k.lower() or search_term.lower() in v.lower()}
    else:
        filtered_terms = glossary_terms
    
    for term, definition in filtered_terms.items():
        with st.expander(f"📘 {term}"):
            st.write(definition)
    
    # Calculation methodologies
    st.subheader("🧮 Calculation Methodologies")
    
    with st.expander("Risk Score Calculation"):
        st.markdown("""
        **Risk Score Components:**
        - **Test Backbone Risk:** Panel (0.8), Exome (1.0), Genome (1.2)
        - **Positioning Risk:** First-line (1.1), Reflex (0.9), Confirmatory (0.7)
        - **Regional Risk:** Varies by payer mix and policies (0.9-1.2)
        - **Specialty Risk:** Based on clinical acceptance (0.8-1.3)
        - **Volume Risk:** Higher volume reduces risk through relationships
        
        **Formula:** Risk Score = Backbone × Positioning × Regional × Specialty × Volume Factor
        """)
    
    with st.expander("Financial Calculations"):
        st.markdown("""
        **Key Formulas:**
        - **Gross Profit** = Reimbursement - Cost per Sample
        - **Effective Reimbursement** = Reimbursement × (1 - Denial Rate)
        - **Net Profit** = Effective Reimbursement - Cost per Sample
        - **ROI** = (Net Profit / Cost per Sample) × 100
        - **Annual Net Profit** = Net Profit × Annual Volume
        - **Collection Rate** = (1 - Denial Rate - Bad Debt Rate) × 100
        """)
    
    with st.expander("Denial Rate Modeling"):
        st.markdown("""
        **Denial Rate Calculation:**
        - **Base Denial Rate** = Risk Score × 15% (industry baseline)
        - **Prior Auth Adjustment** = Base Rate × (1 - Prior Auth Rate × 40%)
        - **Final Rate** = Adjusted Denial Rate + Bad Debt Rate
        
        Prior authorization typically reduces denials by 30-50% through pre-approval.
        """)
    
    # Best practices
    st.subheader("💡 Best Practices")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🎯 Optimization Strategies")
        st.markdown("""
        - **Volume Growth:** Focus on high-volume specialties
        - **Prior Authorization:** Implement for >$500 tests
        - **Clinical Documentation:** Ensure medical necessity
        - **Payer Relations:** Establish coverage policies
        - **Cost Management:** Optimize batch sizes and workflows
        """)
    
    with col2:
        st.markdown("### ⚠️ Risk Mitigation")
        st.markdown("""
        - **Diversify Test Menu:** Reduce single-test dependency
        - **Monitor Denial Trends:** Track by payer and test type
        - **Appeals Process:** Systematic approach to overturns
        - **Financial Counseling:** Reduce bad debt rates
        - **Compliance:** Stay current with coverage policies
        """)
    
    # Contact and support
    st.subheader("📞 Support & Contact")
    st.info("For technical support or questions about this analysis tool, contact your NGS operations team or bioinformatics support.")
    
    # Version information
    st.subheader("ℹ️ Version Information")
    st.markdown("""
    **NGS Reimbursement Intelligence Platform v2.0**
    - Enhanced risk modeling with multi-factor analysis
    - Comprehensive financial projections and scenario planning
    - Monte Carlo simulation capabilities
    - Industry benchmarking integration
    - Advanced workflow comparison tools
    - Automated report generation
    
    *Last updated: June 2025*
    """)

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666; padding: 20px;'>"
    "🧬 NGS Reimbursement Intelligence Platform | "
    "Empowering data-driven decisions in genomic testing operations"
    "</div>", 
    unsafe_allow_html=True
)
