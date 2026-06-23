"""
Portfolio Dashboard – Streamlit recreation of the reference Tableau view.

Run:  streamlit run app.py
"""

import os
from datetime import datetime

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from data_generator import df as generated_df

# ----------------------------------------------------------------------------- 
# Page config & global styling
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Portfolio Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Colour palette inspired by the reference (blue/orange family).
PALETTE = {
    "DOZ": "#f4a259",
    "Site Pz": "#5b8fbf",
    "Site MA": "#9ec4e0",
    "DOM": "#7f8fa6",
    "DOS": "#b0bcc9",
    "DOB": "#2f5d8a",
    "Pharma": "#cfe0ef",
}
CLASS_PALETTE = {
    "Building": "#5bb3a8",
    "Equipment": "#7fc7bd",
    "Infrastr.": "#e89a8f",
    "Other": "#ede3a0",
}
PHASE_ORDER = ["IDEA", "PI", "CD", "BD", "DD", "CC", "CO", "Completed"]

RAG_COLORS = {
    "Green": "#a8d5a2",
    "Amber": "#f2d98d",
    "Red": "#f0a3a3",
    "": "#ffffff",
}

st.markdown(
    """
    <style>
      .block-container {padding-top: 2.8rem; padding-bottom: 1rem; max-width: 100%;}
      header[data-testid="stHeader"] {height: 0; visibility: hidden;}
      h1, h2, h3 {font-family: "Segoe UI", sans-serif;}
      .panel-title {
        background:#eef1f4; border:1px solid #d6dde3; border-radius:4px;
        padding:6px 10px; font-weight:600; font-size:0.95rem; color:#33414e;
        text-align:center; margin-bottom:6px;
      }
      .info-box {
        background:#eef1f4; border:1px solid #d6dde3; border-radius:4px;
        padding:10px; font-size:0.8rem; color:#33414e; text-align:right;
      }
      div[data-testid="stMetricValue"] {font-size:1.4rem;}
      .stButton>button {
        width:100%; border:1px solid #c2ccd6; background:#f3f5f7;
        color:#33414e; font-weight:600;
      }
      .stButton>button:hover {border-color:#5b8fbf; color:#1f3b57;}
    </style>
    """,
    unsafe_allow_html=True,
)


# ----------------------------------------------------------------------------- 
# Data loading
# -----------------------------------------------------------------------------
@st.cache_data
def load_data() -> pd.DataFrame:
    if os.path.exists("portfolio_data.csv"):
        data = pd.read_csv("portfolio_data.csv")
    else:
        data = generated_df.copy()
    # Ensure string columns are not NaN for clean display / filtering
    for col in data.select_dtypes(include="object").columns:
        data[col] = data[col].fillna("")
    return data


df = load_data()

# ----------------------------------------------------------------------------- 
# Session state for filters
# -----------------------------------------------------------------------------
DEFAULTS = {
    "f_org": "(Alle)",
    "f_phase": "(Alle)",
    "f_class": "(Alle)",
}
for k, v in DEFAULTS.items():
    st.session_state.setdefault(k, v)

# Org highlighted by clicking a chart segment (drives table colouring/filter).
st.session_state.setdefault("sel_org", None)


def reset_filters():
    for k, v in DEFAULTS.items():
        st.session_state[k] = v
    st.session_state.sel_org = None


# ----------------------------------------------------------------------------- 
# Header / filter bar
# -----------------------------------------------------------------------------
fc1, fc2, fc3, fc4, fc5 = st.columns([3, 1.4, 3, 3, 2.6])

with fc1:
    st.markdown('<div class="panel-title">Business Organisation</div>', unsafe_allow_html=True)
    org_opts = ["(Alle)"] + sorted(df["Business Organisation"].unique())
    st.selectbox("org", org_opts, key="f_org", label_visibility="collapsed")

with fc2:
    st.markdown("<div style='height:30px'></div>", unsafe_allow_html=True)
    st.button("🔄 Reset All Filters", on_click=reset_filters)

with fc3:
    st.markdown('<div class="panel-title">Project Phase</div>', unsafe_allow_html=True)
    phase_opts = ["(Alle)"] + [p for p in PHASE_ORDER if p in df["Phase"].unique()]
    st.selectbox("phase", phase_opts, key="f_phase", label_visibility="collapsed")

with fc4:
    st.markdown('<div class="panel-title">Project Classification</div>', unsafe_allow_html=True)
    class_opts = ["(Alle)"] + sorted(df["Project Classification"].unique())
    st.selectbox("class", class_opts, key="f_class", label_visibility="collapsed")

with fc5:
    st.markdown(
        f"""
        <div class="info-box">
          *Global pharma projects are not included.<br>
          *Last update: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}
        </div>
        """,
        unsafe_allow_html=True,
    )

# ----------------------------------------------------------------------------- 
# Apply filters
# -----------------------------------------------------------------------------
fdf = df.copy()
if st.session_state.f_org != "(Alle)":
    fdf = fdf[fdf["Business Organisation"] == st.session_state.f_org]
if st.session_state.f_phase != "(Alle)":
    fdf = fdf[fdf["Phase"] == st.session_state.f_phase]
if st.session_state.f_class != "(Alle)":
    fdf = fdf[fdf["Project Classification"] == st.session_state.f_class]

st.markdown("<hr style='margin:8px 0;border-color:#e3e8ec'>", unsafe_allow_html=True)

# ----------------------------------------------------------------------------- 
# Chart row
# -----------------------------------------------------------------------------
c1, c2, c3, c4 = st.columns([2.4, 3.2, 3.4, 2.6])

# --- Donut: Projects / PIs by invest (capex by organisation) -----------------
with c1:
    st.markdown('<div class="panel-title">Projects / PIs by invest</div>', unsafe_allow_html=True)
    inv = (
        fdf.groupby("Business Organisation")["Approved Budget"]
        .sum()
        .reindex(PALETTE.keys())
        .dropna()
    )
    total_capex = inv.sum()
    proj_counts = fdf["Business Organisation"].value_counts()
    pull = [0.06 if o == st.session_state.sel_org else 0 for o in inv.index]
    # Pre-render hover strings (robust vs. customdata indexing on pie traces).
    hovertext = [
        f"<b>Business Organisation: {o}</b><br>"
        f"Capex Volume: {v:,.0f} mEUR<br>"
        f"Percentage of Total Volume: {(v / total_capex * 100):.2f}%<br>"
        f"Projects: {int(proj_counts.get(o, 0))}"
        for o, v in inv.items()
    ]
    fig = go.Figure(
        go.Pie(
            labels=inv.index,
            values=inv.values,
            hole=0.62,
            marker=dict(colors=[PALETTE[o] for o in inv.index]),
            textinfo="label+percent",
            textfont_size=11,
            sort=False,
            pull=pull,
            hovertext=hovertext,
            hovertemplate="%{hovertext}<extra></extra>",
        )
    )
    fig.update_layout(
        showlegend=False,
        margin=dict(t=10, b=10, l=10, r=10),
        height=300,
        hoverlabel=dict(bgcolor="white", font_size=12),
        annotations=[
            dict(
                text=f"Capex Volume<br>in mEUR<br><b>{total_capex:,.0f}</b>",
                x=0.5, y=0.5, font_size=13, showarrow=False,
            )
        ],
    )
    ev = st.plotly_chart(
        fig, use_container_width=True, key="donut_invest",
        on_select="rerun", selection_mode="points",
    )
    _sel = ev.get("selection", {}).get("points", []) if ev else []
    if _sel:
        clicked = _sel[0].get("label")
        if clicked and clicked != st.session_state.sel_org:
            st.session_state.sel_org = clicked
            st.rerun()

# --- Bar: # of projects / PIs per portfolio (grouped by org) -----------------
with c2:
    st.markdown('<div class="panel-title"># of projects / PIs per portfolio</div>', unsafe_allow_html=True)
    cnt = (
        fdf["Business Organisation"]
        .value_counts()
        .reindex(PALETTE.keys())
        .fillna(0)
    )
    capex_by_org = fdf.groupby("Business Organisation")["Approved Budget"].sum()
    bar_custom = [[capex_by_org.get(o, 0)] for o in cnt.index]
    # Emphasise the selected bar via a darker outline.
    line_w = [3 if o == st.session_state.sel_org else 0 for o in cnt.index]
    fig = go.Figure(
        go.Bar(
            x=list(cnt.index),
            y=cnt.values,
            marker_color=[PALETTE[o] for o in cnt.index],
            marker_line=dict(color="#1f3b57", width=line_w),
            text=[int(v) for v in cnt.values],
            textposition="outside",
            customdata=bar_custom,
            hovertemplate=(
                "<b>%{x}</b><br>"
                "Projects: %{y}<br>"
                "Capex Volume: %{customdata[0]:,.0f} mEUR<extra></extra>"
            ),
        )
    )
    fig.update_layout(
        margin=dict(t=20, b=10, l=10, r=10),
        height=300,
        yaxis_title="Number of Projects",
        xaxis_title="",
        showlegend=False,
        hoverlabel=dict(bgcolor="white", font_size=12),
    )
    ev = st.plotly_chart(
        fig, use_container_width=True, key="bar_portfolio",
        on_select="rerun", selection_mode="points",
    )
    _sel = ev.get("selection", {}).get("points", []) if ev else []
    if _sel:
        clicked = _sel[0].get("x")
        if clicked and clicked != st.session_state.sel_org:
            st.session_state.sel_org = clicked
            st.rerun()

# --- Stacked bar: Projects by Phase (stacked by business organisation) -------
with c3:
    st.markdown('<div class="panel-title">Projects by Phase</div>', unsafe_allow_html=True)
    phase_present = [p for p in PHASE_ORDER if p in fdf["Phase"].unique()]
    grp = (
        fdf.groupby(["Phase", "Business Organisation"])
        .size()
        .reset_index(name="n")
    )
    fig = go.Figure()
    for org, color in PALETTE.items():
        sub = grp[grp["Business Organisation"] == org]
        ymap = {p: 0 for p in phase_present}
        for _, r in sub.iterrows():
            if r["Phase"] in ymap:
                ymap[r["Phase"]] = r["n"]
        fig.add_bar(
            x=phase_present,
            y=[ymap[p] for p in phase_present],
            name=org,
            marker_color=color,
            hovertemplate=(
                "<b>Phase: %{x}</b><br>"
                f"Business Organisation: {org}<br>"
                "Projects: %{y}<extra></extra>"
            ),
        )
    # totals as annotations on top
    totals = fdf["Phase"].value_counts().reindex(phase_present).fillna(0)
    for p in phase_present:
        fig.add_annotation(
            x=p, y=totals[p], text=str(int(totals[p])),
            showarrow=False, yshift=10, font_size=11,
        )
    fig.update_layout(
        barmode="stack",
        margin=dict(t=20, b=70, l=10, r=10),
        height=320,
        yaxis_title="Number of Projects",
        xaxis=dict(
            type="category",
            categoryorder="array",
            categoryarray=phase_present,
            tickangle=0,
        ),
        legend=dict(
            orientation="h", yanchor="top", y=-0.22,
            xanchor="center", x=0.5, font_size=9,
        ),
        hoverlabel=dict(bgcolor="white", font_size=12),
    )
    st.plotly_chart(fig, use_container_width=True, key="bar_phase")

# --- Donut: Project Classification -------------------------------------------
with c4:
    st.markdown('<div class="panel-title">Project Classification</div>', unsafe_allow_html=True)
    cls_cnt = (
        fdf["Project Classification"]
        .value_counts()
        .reindex(CLASS_PALETTE.keys())
        .dropna()
    )
    cls_budget = fdf.groupby("Project Classification")["Approved Budget"].sum()
    cls_total = cls_cnt.sum()
    cls_hover = [
        f"<b>Classification: {c}</b><br>"
        f"Projects: {int(n)}<br>"
        f"Share: {(n / cls_total * 100):.2f}%<br>"
        f"Capex Volume: {cls_budget.get(c, 0):,.0f} mEUR"
        for c, n in cls_cnt.items()
    ]
    fig = go.Figure(
        go.Pie(
            labels=cls_cnt.index,
            values=cls_cnt.values,
            hole=0.62,
            marker=dict(colors=[CLASS_PALETTE[c] for c in cls_cnt.index]),
            textinfo="label+value",
            textfont_size=11,
            sort=False,
            hovertext=cls_hover,
            hovertemplate="%{hovertext}<extra></extra>",
        )
    )
    fig.update_layout(
        showlegend=False,
        margin=dict(t=10, b=10, l=10, r=10),
        height=300,
        hoverlabel=dict(bgcolor="white", font_size=12),
        annotations=[
            dict(
                text=f"Projects / PIs<br><b>{int(cls_cnt.sum())}</b>",
                x=0.5, y=0.5, font_size=13, showarrow=False,
            )
        ],
    )
    st.plotly_chart(fig, use_container_width=True, key="donut_class")

st.markdown("<hr style='margin:8px 0;border-color:#e3e8ec'>", unsafe_allow_html=True)

# ----------------------------------------------------------------------------- 
# Detail table with RAG colouring on PMR columns
# -----------------------------------------------------------------------------
# A chart click selects an organisation -> the table is filtered to it and the
# rows are tinted with that organisation's colour.
sel_org = st.session_state.sel_org
tdf = fdf.copy()
if sel_org and sel_org in tdf["Business Organisation"].values:
    tdf = tdf[tdf["Business Organisation"] == sel_org]

th1, th2 = st.columns([6, 1])
with th1:
    if sel_org:
        chip = PALETTE.get(sel_org, "#5b8fbf")
        st.markdown(
            f'<div class="panel-title" style="text-align:left">'
            f'Project Details — <span style="background:{chip};padding:2px 8px;'
            f'border-radius:4px;color:#1f3b57">{sel_org}</span> — {len(tdf)} projects</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<div class="panel-title" style="text-align:left">Project Details — '
            f'{len(tdf)} projects <span style="font-weight:400;color:#7f8fa6">'
            f'(click a chart segment to filter by organisation)</span></div>',
            unsafe_allow_html=True,
        )
with th2:
    if sel_org:
        st.button("✖ Clear selection", on_click=lambda: st.session_state.update(sel_org=None))

money_cols = [
    "Approved Budget", "Total Actuals", "FFC",
    "Actuals Current Year", "Forecast Current Year",
]
rag_cols = ["PMR Overall", "PMR Schedule", "PMR Cost"]

show = tdf.copy()


def fmt_money(v):
    try:
        return f"{float(v):,.2f}M €".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        return v


for col in money_cols:
    show[col] = show[col].apply(fmt_money)


def style_rag(val):
    color = RAG_COLORS.get(str(val), "#ffffff")
    return f"background-color:{color}; color:transparent;" if val else "background-color:#ffffff;"


def _hex_to_tint(hex_color, alpha=0.22):
    """Blend a hex colour toward white to get a light row tint."""
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
    r = int(r + (255 - r) * (1 - alpha))
    g = int(g + (255 - g) * (1 - alpha))
    b = int(b + (255 - b) * (1 - alpha))
    return f"rgb({r},{g},{b})"


styler = (
    show.style
    .map(style_rag, subset=rag_cols)
    .set_properties(**{"font-size": "11px"})
    .set_table_styles(
        [
            {"selector": "th", "props": [("background-color", "#f3f5f7"),
                                         ("color", "#33414e"),
                                         ("font-size", "11px"),
                                         ("text-align", "left")]},
        ]
    )
)

# When an organisation is selected, tint every (non-RAG) cell with its colour.
if sel_org:
    tint = _hex_to_tint(PALETTE.get(sel_org, "#5b8fbf"))
    non_rag = [c for c in show.columns if c not in rag_cols]
    styler = styler.set_properties(
        subset=non_rag, **{"background-color": tint}
    )

st.dataframe(styler, use_container_width=True, height=430, hide_index=True)

# ----------------------------------------------------------------------------- 
# Footer KPIs
# -----------------------------------------------------------------------------
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Projects / PIs", f"{len(tdf)}")
k2.metric("Approved Budget", f"{tdf['Approved Budget'].sum():,.0f} mEUR")
k3.metric("Total Actuals", f"{tdf['Total Actuals'].sum():,.0f} mEUR")
k4.metric("FFC", f"{tdf['FFC'].sum():,.0f} mEUR")
k5.metric("Forecast Curr. Year", f"{tdf['Forecast Current Year'].sum():,.1f} mEUR")
