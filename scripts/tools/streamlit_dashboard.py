#!/usr/bin/env python3
"""
WNBA Betting Intelligence Dashboard
Real-time visualization of phase performance, confidence levels, and betting recommendations.

Run with: streamlit run streamlit_dashboard.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os

# Page config
st.set_page_config(
    page_title="WNBA Phase Intelligence",
    page_icon="🏀",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main {
        padding-top: 2rem;
    }
    .stMetric {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
        margin: 5px;
    }
    .success {
        color: #28a745;
    }
    .warning {
        color: #ffc107;
    }
    .danger {
        color: #dc3545;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    """Load all relevant data files."""
    data = {}
    
    files = {
        'phase_results': 'phase_results_tracker.csv',
        'confidence': 'output/phase_confidence_levels.csv',
        'kelly_divisors': 'output/dynamic_kelly_divisors.csv',
        'risk_adjustments': 'output/phase_risk_adjustments.csv',
        'betting_card': 'input/daily_betting_card.csv'
    }
    
    for key, filepath in files.items():
        if os.path.exists(filepath):
            try:
                data[key] = pd.read_csv(filepath)
            except:
                data[key] = pd.DataFrame()
        else:
            data[key] = pd.DataFrame()
    
    return data

def create_phase_summary(data):
    """Create phase performance summary."""
    st.header("🌙 Phase Performance Overview")
    
    if data['phase_results'].empty:
        st.warning("No phase results data available")
        return
    
    phases = ['luteal', 'menstrual', 'follicular', 'ovulatory']
    cols = st.columns(4)
    
    for idx, phase in enumerate(phases):
        with cols[idx]:
            phase_data = data['phase_results'][data['phase_results']['phase'] == phase]
            
            if len(phase_data) > 0:
                wins = len(phase_data[phase_data['actual_result'] == 'win'])
                total = len(phase_data)
                win_rate = wins / total if total > 0 else 0
                
                # Color based on performance
                if win_rate >= 0.65:
                    color = "success"
                elif win_rate >= 0.55:
                    color = "warning"
                else:
                    color = "danger"
                
                st.metric(
                    label=f"{phase.capitalize()} Phase",
                    value=f"{win_rate:.1%} WR",
                    delta=f"{wins}W - {total-wins}L"
                )
                
                # Progress bar for bet count
                progress = min(total / 30, 1.0)  # 30 bets = full bar
                st.progress(progress)
                st.caption(f"{total} bets")
            else:
                st.metric(
                    label=f"{phase.capitalize()} Phase",
                    value="No Data",
                    delta="0 bets"
                )

def create_confidence_chart(data):
    """Create confidence level visualization."""
    st.header("📊 Confidence Levels by Phase")
    
    if data['confidence'].empty:
        st.info("No confidence data available yet")
        return
    
    # Create bar chart
    fig = px.bar(
        data['confidence'],
        x='phase',
        y='confidence_score',
        color='confidence_level',
        color_discrete_map={
            'HIGH': '#28a745',
            'MEDIUM': '#ffc107',
            'LOW': '#dc3545',
            'INSUFFICIENT': '#6c757d'
        },
        title="Phase Confidence Scores",
        labels={'confidence_score': 'Confidence Score', 'phase': 'Phase'}
    )
    
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)

def create_kelly_divisor_table(data):
    """Display Kelly divisor recommendations."""
    st.header("🎯 Dynamic Kelly Divisors")
    
    if data['kelly_divisors'].empty:
        st.info("No Kelly divisor data available")
        return
    
    # Format the dataframe
    display_df = data['kelly_divisors'][
        ['phase', 'kelly_divisor', 'win_rate', 'bet_count', 'confidence_level']
    ].copy()
    
    display_df['win_rate'] = (display_df['win_rate'] * 100).round(1).astype(str) + '%'
    display_df['kelly_divisor'] = display_df['kelly_divisor'].round(2)
    
    # Rename columns for display
    display_df.columns = ['Phase', 'Kelly Divisor', 'Win Rate', 'Bet Count', 'Confidence']
    
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )

def create_bet_timeline(data):
    """Create timeline of bets by phase."""
    st.header("📈 Betting Activity Timeline")
    
    if data['phase_results'].empty:
        st.info("No betting history available")
        return
    
    # Convert date column
    df = data['phase_results'].copy()
    df['date'] = pd.to_datetime(df['date'])
    
    # Group by date and phase
    timeline = df.groupby(['date', 'phase']).size().reset_index(name='bet_count')
    
    # Create line chart
    fig = px.line(
        timeline,
        x='date',
        y='bet_count',
        color='phase',
        title="Daily Bet Count by Phase",
        markers=True
    )
    
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)

def create_risk_matrix(data):
    """Create risk adjustment matrix."""
    st.header("⚖️ Risk Adjustment Matrix")
    
    if data['risk_adjustments'].empty:
        st.info("No risk adjustment data available")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Risk level distribution
        fig = px.pie(
            data['risk_adjustments'],
            names='risk_level',
            title="Risk Level Distribution",
            color_discrete_map={
                'HIGH': '#28a745',
                'MEDIUM': '#ffc107',
                'LOW': '#dc3545',
                'INSUFFICIENT': '#6c757d'
            }
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Kelly multiplier comparison
        fig = px.bar(
            data['risk_adjustments'],
            x='phase',
            y='kelly_multiplier',
            color='risk_level',
            title="Kelly Multipliers by Phase",
            color_discrete_map={
                'HIGH': '#28a745',
                'MEDIUM': '#ffc107',
                'LOW': '#dc3545',
                'INSUFFICIENT': '#6c757d'
            }
        )
        st.plotly_chart(fig, use_container_width=True)

def create_today_card(data):
    """Display today's betting card."""
    st.header("📋 Today's Betting Card")
    
    if data['betting_card'].empty:
        st.info("No bets loaded for today")
        return
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Bets", len(data['betting_card']))
    
    with col2:
        if 'confidence' in data['betting_card'].columns:
            avg_conf = data['betting_card']['confidence'].mean()
            st.metric("Avg Confidence", f"{avg_conf:.1%}")
        elif 'kelly_fraction' in data['betting_card'].columns:
            avg_kelly = data['betting_card']['kelly_fraction'].mean()
            st.metric("Avg Kelly", f"{avg_kelly:.3f}")
    
    with col3:
        if 'bet_percentage' in data['betting_card'].columns:
            total_stake = data['betting_card']['bet_percentage'].sum()
            st.metric("Total Stake", f"{total_stake:.2%}")
        elif 'recommended_bet_size' in data['betting_card'].columns:
            total_stake = data['betting_card']['recommended_bet_size'].sum()
            st.metric("Total Stake", f"{total_stake:.2%}")
        else:
            st.metric("Total Stake", "N/A")
    
    with col4:
        if 'adv_phase' in data['betting_card'].columns:
            phases = data['betting_card']['adv_phase'].value_counts()
            dominant_phase = phases.index[0] if len(phases) > 0 else "N/A"
            st.metric("Dominant Phase", dominant_phase.capitalize())
        elif 'phase' in data['betting_card'].columns:
            phases = data['betting_card']['phase'].value_counts()
            dominant_phase = phases.index[0] if len(phases) > 0 else "N/A"
            st.metric("Dominant Phase", dominant_phase.capitalize())
        else:
            st.metric("Dominant Phase", "N/A")
    
    # Bet details
    st.subheader("Bet Details")
    
    # Check which columns are available
    available_cols = data['betting_card'].columns.tolist()
    
    # Map to expected columns
    display_cols = []
    if 'player_name' in available_cols:
        display_cols.append('player_name')
    elif 'player' in available_cols:
        display_cols.append('player')
    
    if 'stat_type' in available_cols:
        display_cols.append('stat_type')
    elif 'market' in available_cols:
        display_cols.append('market')
    
    if 'line' in available_cols:
        display_cols.append('line')
    
    if 'adjusted_prediction' in available_cols:
        display_cols.append('adjusted_prediction')
    elif 'prediction' in available_cols:
        display_cols.append('prediction')
    
    if 'kelly_fraction' in available_cols:
        display_cols.append('kelly_fraction')
    
    if 'adv_phase' in available_cols:
        display_cols.append('adv_phase')
    elif 'phase' in available_cols:
        display_cols.append('phase')
    
    if 'bet_percentage' in available_cols:
        display_cols.append('bet_percentage')
    elif 'recommended_bet_size' in available_cols:
        display_cols.append('recommended_bet_size')
    
    if display_cols:
        st.dataframe(
            data['betting_card'][display_cols],
            use_container_width=True,
            hide_index=True
        )

def main():
    """Main dashboard application."""
    st.title("🏀 WNBA Phase Intelligence Dashboard")
    st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Load data
    data = load_data()
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # Mode indicator
        mode = st.radio(
            "System Mode",
            ["Testing", "Production"],
            help="Toggle between testing and production thresholds"
        )
        
        st.divider()
        
        # Quick stats
        st.subheader("📊 Quick Stats")
        if not data['phase_results'].empty:
            total_bets = len(data['phase_results'])
            total_wins = len(data['phase_results'][
                data['phase_results']['actual_result'] == 'win'
            ])
            overall_wr = total_wins / total_bets if total_bets > 0 else 0
            
            st.metric("Total Bets", total_bets)
            st.metric("Overall Win Rate", f"{overall_wr:.1%}")
            st.metric("System Status", "🟢 Active")
        
        st.divider()
        
        # Links
        st.subheader("🔗 Quick Actions")
        if st.button("Run Integrity Check"):
            st.info("Run `python log_integrity_check.py`")
        if st.button("Update Phase Multipliers"):
            st.info("Run `python phase_multiplier_engine.py`")
        if st.button("Generate Checklist"):
            st.info("Run `python checklist_generator.py`")
    
    # Main content
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Overview", 
        "🎯 Confidence", 
        "⚖️ Risk Management",
        "📋 Today's Card"
    ])
    
    with tab1:
        create_phase_summary(data)
        create_bet_timeline(data)
    
    with tab2:
        create_confidence_chart(data)
        create_kelly_divisor_table(data)
    
    with tab3:
        create_risk_matrix(data)
    
    with tab4:
        create_today_card(data)
    
    # Footer
    st.divider()
    st.caption("Built with Streamlit • WNBA Phase Intelligence System")

if __name__ == "__main__":
    main()