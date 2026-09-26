"""교과서식 근축 광선 추적 시뮬레이터."""
import math

import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="광선 추적 실험실", layout="wide", initial_sidebar_state="collapsed")
st.markdown("""<style>
@media (min-width: 700px) and (max-width: 1200px) {
  .block-container { padding-top: 1rem; padding-left: 1.2rem; padding-right: 1.2rem; max-width: 100%; }
  h1 { font-size: 1.8rem !important; }
  div[data-testid="stRadio"] label, div[data-testid="stSelectbox"] label { font-size: 1rem; }
  .stPlotlyChart { width: 100%; }
}
@media (max-width: 699px) {
  .block-container { padding-top: .75rem; padding-left: .65rem; padding-right: .65rem; }
  h1 { font-size: 1.45rem !important; }
}
</style>""", unsafe_allow_html=True)
st.title("🔎 광선 추적 실험실")
st.caption("물체의 위치와 높이, 초점 거리를 바꾸며 다섯 광학 기기의 상을 비교해 보세요. 빛은 왼쪽에서 오른쪽으로 진행합니다.")

KINDS = ["볼록렌즈", "오목렌즈", "평면거울", "볼록거울", "오목거울"]
kind = st.radio("광학 기기", KINDS, horizontal=True)
left, middle, right = st.columns(3, gap="medium")
with left:
    d = st.slider("물체 거리", 2.0, 24.0, 12.0, 0.1)
with middle:
    f_abs = st.slider("초점 거리", 2.0, 12.0, 6.0, 0.1, disabled=kind == "평면거울",
                      help="곡면거울의 초점 거리는 곡률반지름의 절반입니다.")
with right:
    h = st.slider("물체 높이", 0.5, 5.0, 2.5, 0.1)
with st.expander("표시 설정", expanded=False):
    count = st.select_slider("표시할 광선 수 (최대 3개)", options=[1, 2, 3], value=3)

mirror = "거울" in kind
f = (f_abs if kind in ("볼록렌즈", "오목거울") else -f_abs) if kind != "평면거울" else math.inf
# 렌즈/거울 방정식: 1/f = 1/d + 1/q. q>0은 실제 빛의 진행 방향에 있는 실상.
den = (0 if math.isinf(f) else 1 / f) - 1 / d
at_infinity = abs(den) < 1e-8
q = math.inf if at_infinity else 1 / den
m = math.inf if at_infinity else -q / d
xi = (-q if mirror else q) if not at_infinity else math.inf
yi = m * h if not at_infinity else math.inf

if kind == "평면거울":
    description = "평면거울은 물체와 같은 크기의 정립 허상을 거울 뒤의 같은 거리에 만듭니다."
elif at_infinity:
    description = "물체가 초점에 있어 반사·굴절한 광선이 서로 평행합니다. 유한한 거리에는 상이 맺히지 않습니다."
else:
    reality = "실상" if q > 0 else "허상"
    attitude = "정립" if m > 0 else "도립"
    description = f"{kind}: {attitude} {reality}, 배율 {abs(m):.2f}배. " + ("실선이 실제 광선이고, 점선은 뒤로 연장한 선입니다." if q < 0 else "실선 광선이 상에서 만납니다.")
st.info(description)

colors = ["#ef4444", "#0ea5e9", "#16a34a"]
fig = go.Figure()

def segment(a, b, color, dash="solid", width=2.5, name=None):
    fig.add_trace(go.Scatter(x=[a[0], b[0]], y=[a[1], b[1]], mode="lines",
                             line=dict(color=color, width=width, dash=dash),
                             name=name, hoverinfo="skip", showlegend=bool(name)))

def marker(x, name, color="#64748b", y=-0.28):
    fig.add_trace(go.Scatter(x=[x], y=[0], mode="markers+text", text=[name],
                             textposition="bottom center", textfont=dict(color=color, size=14),
                             marker=dict(size=7, color=color), showlegend=False, hovertemplate=f"{name}: %{{x:.1f}}<extra></extra>"))

def arrow(x, y, height, color, name):
    segment((x, 0), (x, height), color, width=5, name=name)
    fig.add_annotation(x=x, y=height, ax=x, ay=0, xref="x", yref="y", axref="x", ayref="y",
                       showarrow=True, arrowhead=2, arrowsize=1.3, arrowwidth=2, arrowcolor=color)

# 평면거울은 입사각이 다른 세 광선; 구면 기기는 평행/중심 또는 구심/초점 광선.
if kind == "평면거울":
    hits = [h * 0.8, h * 0.25, -h * 0.4]
elif mirror:
    hits = [h, 0.0, h / 2]  # 2번 광선은 구심 방향으로 재계산
    if kind != "평면거울":
        c = -2 * f  # 거울의 구심: 오목은 왼쪽, 볼록은 오른쪽
        hits[1] = h * (0 - c) / (-d - c) if abs(-d - c) > 1e-8 else None
        # 물체가 구심에 위치하면 그 광선은 광축과 겹치므로 다른 광선으로 대체.
        if hits[1] is None or abs(hits[1]) > 1e4:
            hits[1] = h / 3
else:
    hits = [h, 0.0, h * f_abs / (d + f_abs)] if kind == "오목렌즈" else [h, 0.0, h * f_abs / (f_abs - d) if abs(f_abs-d)>1e-8 else h/2]
    # 3번 광선은 전방 초점을 향하는 선 (초점에 물체가 있으면 대체).
    if kind == "볼록렌즈" and abs(d-f_abs)>1e-8 and abs(hits[2]) > 5*h:
        hits[2] = h/2

# 세 번째 광선의 출사 방향은 같은 상을 지나는 직선으로 결정한다.
xlim = min(85.0, max(27.0, d + 5, abs(xi) * 1.17 if math.isfinite(xi) else 35.0, 2*f_abs+5))
ymax = min(38.0, max(5.5, h * 1.8, abs(yi) * 1.17 if math.isfinite(yi) else h*3))
segment((-xlim, 0), (xlim, 0), "#94a3b8", dash="dot", width=1.5, name="광축")
if mirror:
    segment((0, -ymax), (0, ymax), "#475569", width=4, name=kind)
    fig.add_annotation(x=0, y=ymax*0.94, text="거울 뒤 →", showarrow=False, font=dict(color="#64748b"), xanchor="left")
else:
    segment((0, -ymax), (0, ymax), "#6366f1", width=4, name=kind)
    marker(0, "O (광학 중심)")
    marker(-f_abs if f > 0 else f_abs, "F₁")
    marker(f_abs if f > 0 else -f_abs, "F₂")
if mirror:
    marker(0, "V (거울 중심)")
    if kind != "평면거울":
        marker(-f, "F")
        marker(-2*f, "C (구심)")

arrow(-d, h, "#1d4ed8", "물체")
if not at_infinity and abs(xi) <= xlim and abs(yi) <= ymax:
    arrow(xi, yi, "#a855f7", "상")

for idx, hit in enumerate(hits[:count]):
    color = colors[idx]
    source, surface = (-d, h), (0, hit)
    segment(source, surface, color, name=f"광선 {idx+1}")
    if mirror:
        # 평면거울 포함: q로부터 얻은 반사 광선의 기울기.
        if at_infinity:
            slope = (hit - h) / d
        else:
            slope = (yi - hit) / (xi if abs(xi) > 1e-8 else -1e-8)
        segment(surface, (-xlim, hit - slope*xlim), color)
        if not at_infinity and q < 0:
            segment(surface, (min(xlim, xi*1.14), hit + slope*min(xlim, xi*1.14)), color, "dash", 1.6)
    else:
        slope = (yi - hit) / xi if not at_infinity and abs(xi)>1e-8 else (hit-h)/d - hit/f
        segment(surface, (xlim, hit + slope*xlim), color)
        if not at_infinity and q < 0:
            segment(surface, (max(-xlim, xi*1.14), hit + slope*max(-xlim, xi*1.14)), color, "dash", 1.6)

fig.update_layout(height=510, margin=dict(l=12,r=12,t=45,b=35),
                  xaxis=dict(range=[-xlim,xlim], title="광축 방향 거리 (임의 단위)", zeroline=False),
                  yaxis=dict(range=[-ymax,ymax], scaleanchor="x", scaleratio=1, zeroline=False, title="높이"),
                  legend=dict(orientation="h", y=1.12, font=dict(size=11)), template="plotly_white",
                  dragmode="pan")
st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False, "scrollZoom": False,
                                                    "responsive": True})
if not at_infinity:
    st.latex(r"\frac{1}{f}=\frac{1}{d_o}+\frac{1}{d_i}\qquad m=-\frac{d_i}{d_o}")
    st.caption(f"물체 거리 dₒ={d:.1f}, 상 거리 dᵢ={q:.1f}, 상 높이={yi:.1f} (부호는 빛의 실제 진행 방향 기준). 거울은 그림의 왼쪽이 앞쪽이므로 상 좌표 x=−dᵢ입니다.")
else:
    st.caption("초점에 놓인 물체: 상 거리와 배율은 무한대로 발산합니다.")
st.markdown("**광선 읽는 법**  빨강: 광축에 평행한 입사광 · 파랑: 중심/구심을 향하는 입사광 · 초록: 다른 경로의 입사광. 평면거울은 서로 다른 세 입사각을 표시합니다. 점선은 허상으로 향하는 역연장선입니다.")
st.caption("구면 렌즈와 거울의 근축 광선 모델입니다. 실제 기기의 두께, 구면 수차, 거울 면의 곡률에 따른 입사 위치는 생략했습니다.")
