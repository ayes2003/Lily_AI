import streamlit as st
import plotly.graph_objects as go
import datetime

def inject_custom_css():
    """Forces High-Contrast OLED Black Theme with Warm Orchard accents."""
    st.markdown("""
        <style>
        /* Global Background */
        [data-testid="stAppViewContainer"] { background-color: #000000 !important; }
        [data-testid="stHeader"] { background: rgba(0,0,0,0); }
        [data-testid="stSidebar"] { background-color: #0D1117 !important; border-right: 1px solid #1C2128; }

        /* Warm Orchard Card Logic */
        .warm-card {
            background-color: #0D1117 !important;
            padding: 25px;
            border-radius: 25px;
            border: 1px solid #1C2128;
            margin-bottom: 20px;
            color: #C9D1D9 !important;
        }

        /* Banner Styling */
        .hero-banner {
            background: linear-gradient(135deg, #FF7E7E 0%, #B33F3F 100%);
            padding: 40px;
            border-radius: 30px;
            margin-bottom: 30px;
            color: white !important;
        }

        /* KPI Cards */
        .stat-card {
            background-color: #161B22;
            border-radius: 20px;
            padding: 15px;
            text-align: center;
            border: 1px solid #30363D;
        }
        .stat-number { font-size: 32px; font-weight: 800; color: #FF7E7E; display: block; }
        .stat-label { color: #8B949E; font-size: 14px; }

        /* Mood Display */
        .mood-emoji-large {
            font-size: 100px;
            margin: 30px 0;
            display: block;
        }

        /* Schedule Item */
        .schedule-item {
            display: flex;
            align-items: center;
            padding: 15px 0;
            border-bottom: 1px solid #1C2128;
        }
        .schedule-icon {
            background: #1C2128;
            padding: 12px;
            border-radius: 15px;
            margin-right: 15px;
            font-size: 22px;
        }

        /* Insight Box */
        .insight-box {
            background-color: #064E3B;
            border-radius: 15px;
            padding: 15px;
            border: 1px solid #065F46;
            color: #D1FAE5;
            font-size: 14px;
            margin-top: 15px;
        }
        </style>
        """, unsafe_allow_html=True)

def hero_banner(name):
    """Dynamic Welcome Banner."""
    now = datetime.datetime.now()
    greeting = "Good Morning" if now.hour < 12 else "Good Afternoon" if now.hour < 17 else "Good Evening"
    date_str = now.strftime("%A, %B %d")
    
    st.markdown(f"""
        <div class="hero-banner">
            <span style="font-size:14px; opacity:0.8; font-weight:600;">{date_str}</span>
            <h1 style="color:white !important; margin:5px 0 0 0; font-size:38px;">{greeting}, {name}! 🌸</h1>
            <p style="color:white !important; opacity:0.9; margin-top:10px;">Lily is here and has been thinking of you all day.</p>
        </div>
    """, unsafe_allow_html=True)

def kpi_row(days, memories, chats, wellness):
    """Row of 4 high-contrast cards."""
    c1, c2, c3, c4 = st.columns(4)
    metrics = [
        {"icon": "❤️", "val": days, "lab": "Days Together"},
        {"icon": "📔", "val": memories, "lab": "Memories Saved"},
        {"icon": "💬", "val": chats, "lab": "Chats Today"},
        {"icon": "📈", "val": wellness, "lab": "Wellness Score"}
    ]
    for i, m in enumerate(metrics):
        with [c1, c2, c3, c4][i]:
            st.markdown(f"""
                <div class="stat-card">
                    <span style="font-size:22px;">{m['icon']}</span><br>
                    <span class="stat-number">{m['val']}</span>
                    <span class="stat-label">{m['lab']}</span>
                </div>
            """, unsafe_allow_html=True)

def wellness_chart(data_points):
    """OLED-friendly chart with DYNAMIC day labels."""
    scores = data_points if data_points else [0]*7
    today = datetime.date.today()
    days = [(today - datetime.timedelta(days=i)).strftime("%a") for i in range(6, -1, -1)]
    
    emojis = ['🤩' if s > 85 else '😊' if s > 70 else '😐' if s > 50 else '😔' for s in scores]
    
    max_score = max(scores) if any(scores) else 0
    colors = ['#FF4B4B' if s == max_score and s > 0 else '#FF7E7E' for s in scores]

    fig = go.Figure(go.Bar(
        x=days, y=scores,
        marker=dict(color=colors, opacity=0.8, line_width=0),
        text=emojis, textposition='outside', textfont=dict(size=20, color="white")
    ))
    
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        height=300, margin=dict(l=0,r=0,t=40,b=0),
        yaxis=dict(visible=False, range=[0, 125]),
        xaxis=dict(tickfont=dict(color='#8B949E', size=14), showgrid=False)
    )
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

def schedule_list(habits):
    """Returns the schedule as a single HTML string with NO leading indentation."""
    html = "<h3 style='color:#F0F6FC; margin-bottom:20px;'>Today's Schedule 🔔</h3>"
    
    if not habits:
        return html + "<p style='color:#8B949E;'>No tasks scheduled for today.</p>"
    
    for h in habits[:5]:
        lbl = h.get('label', '').lower()
        icon = "💊" if "med" in lbl else "🚶" if "walk" in lbl else "🍱" if "lunch" in lbl or "eat" in lbl else "🗓️"
        done_status = "✅" if h.get('done') else "⭕"
        
        # 🚀 NO INDENTATION: HTML is on a single flat line to avoid the 'Code View' bug
        item_html = f'<div class="schedule-item"><div class="schedule-icon">{icon}</div><div style="flex-grow:1;"><b style="color:#C9D1D9; font-size:16px;">{h.get("label", "Task")}</b><br><span style="color:#8B949E; font-size:13px;">{h.get("time", "Today")}</span></div><div style="font-size:20px;">{done_status}</div></div>'
        html += item_html
        
    return html