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

def arrow(x, height, color, name):
    segment((x, 0), (x, height), color, width=5, name=name)
    fig.add_annotation(x=x, y=height, ax=x, ay=0, xref="x", yref="y", axref="x", ayref="y",
                       showarrow=True, arrowhead=2, arrowsize=1.3, arrowwidth=2, arrowcolor=color)

# 평면거울은 입사각이 다른 세 광선. 나머지는 평행 광선과 두 경로의 광선.
if kind == "평면거울":
    hits = [h * 0.8, h * 0.25, -h * 0.4]
else:
    hits = [h, 0.0, h / 2]

# 세 번째 광선의 출사 방향은 같은 상을 지나는 직선으로 결정한다.
xlim = min(85.0, max(27.0, d + 5, abs(xi) * 1.17 if math.isfinite(xi) else 35.0, 2*f_abs+5))
ymax = min(38.0, max(5.5, h * 1.8, abs(yi) * 1.17 if math.isfinite(yi) else h*3))
segment((-xlim, 0), (xlim, 0), "#94a3b8", dash="dot", width=1.5, name="광축")
device_h = min(ymax * .83, max(3.4, h * 1.45))
ys = [device_h * (i - 40) / 40 for i in range(81)]
if mirror:
    curvature = -0.72 if kind == "오목거울" else (0.72 if kind == "볼록거울" else 0)
    edge = [curvature * (y / device_h) ** 2 for y in ys]
    fig.add_trace(go.Scatter(x=edge, y=ys, mode="lines", line=dict(color="#334155", width=7),
                             name=kind, hoverinfo="skip"))
    for y in ys[::10]:
        x = curvature * (y / device_h) ** 2
        segment((x + .13, y - .15), (x + .49, y + .23), "#94a3b8", width=1.3)
    fig.add_annotation(x=0.9, y=device_h + .5, text="거울 뒤 →", showarrow=False,
                       font=dict(color="#64748b", size=13), xanchor="left")
else:
    thickness = [(.22 + .65 * (1 - (y / device_h) ** 2)) if kind == "볼록렌즈"
                 else (.20 + .65 * (y / device_h) ** 2) for y in ys]
    fig.add_trace(go.Scatter(x=[-v for v in thickness] + list(reversed(thickness)),
                             y=ys + list(reversed(ys)), fill="toself", mode="lines",
                             line=dict(color="#2563eb", width=2.5), fillcolor="rgba(125,211,252,.45)",
                             name=kind, hoverinfo="skip"))
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
        # 근축 근사에서 반사광 기울기. x<0이 거울 앞쪽이다.
        slope = (h - hit) / d + (0 if math.isinf(f) else hit / f)
        segment(surface, (-xlim, hit - slope*xlim), color)
        if not at_infinity and q < 0:
            segment(surface, (min(xlim, xi*1.14), hit + slope*min(xlim, xi*1.14)), color, "dash", 1.6)
    else:
        slope = (hit-h)/d - hit/f
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
st.markdown("**그림 읽는 법**  파란 화살표는 물체, 보라 화살표는 상입니다. 빨강·하늘·초록색은 세 경로의 광선이며, 점선은 허상을 찾기 위한 역연장선입니다. F는 초점, C는 구심, O는 렌즈의 중심, V는 거울의 중심입니다.")
st.caption("그림의 렌즈 굴곡과 거울 곡면은 형태를 알아보기 위한 모식도입니다. 광선은 중심 x=0에서 꺾이는 근축 근사로 계산하므로 실제 곡면과 교차하는 지점은 정밀하게 반영되지 않습니다.")
