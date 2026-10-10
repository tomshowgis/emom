"""Dash app: record sets over BLE and browse recordings with per-axis plots.

Run:  .venv/bin/python repcounter/tools/recorder_app.py   (from the terminal, not a sandbox)
Then open http://127.0.0.1:8050 in Chrome.
"""
from __future__ import annotations

import itertools
import time

import plotly.graph_objects as go
from dash import Dash, Input, Output, State, ctx, dcc, html, no_update
from plotly.subplots import make_subplots

from .ble_stream import BleStreamer
from .exercises import MOUNTS, load_exercises
from .storage import list_sessions, load_session, samples_to_df, save_session

STREAM = BleStreamer(buffer_seconds=900)
REC = {"active": False, "t0": 0.0, "pending": None}  # pending = samples waiting for the save form

EXERCISES = load_exercises()
AXES = [("ax", "acc X [m/s²]"), ("ay", "acc Y [m/s²]"), ("az", "acc Z [m/s²]"), ("a_mag", "|acc| [m/s²]"),
        ("gx", "gyro X [rad/s]"), ("gy", "gyro Y [rad/s]"), ("gz", "gyro Z [rad/s]"), ("g_mag", "|gyro| [rad/s]")]
COLORS = ["#1f77b4", "#d62728", "#2ca02c", "#9467bd", "#ff7f0e", "#17becf"]

app = Dash(__name__, title="EMOM rep recorder")


TARGET_SETS = 5
START_SIX = ["biceps-curl", "situp-press", "side-drags", "russian-swing", "cal-pushup", "cal-pullup"]


def set_counts() -> dict[str, int]:
    """Recorded sets per exercise id (only sets with at least one real rep)."""
    counts: dict[str, int] = {}
    for m in list_sessions():
        if (m.get("true_reps") or 0) > 0:
            counts[m["exercise_id"]] = counts.get(m["exercise_id"], 0) + 1
    return counts


def exercise_options() -> list[dict]:
    counts = set_counts()
    opts = []
    for i, n in EXERCISES:
        c = counts.get(i, 0)
        mark = "✅ " if c >= TARGET_SETS else ("● " if c else "")
        opts.append({"label": f"{mark}{n}" + (f" · {c}/{TARGET_SETS} serii" if c else ""), "value": i})
    return opts


def progress_text() -> str:
    counts = set_counts()
    names = dict(EXERCISES)
    parts = [f"{names.get(i, i)} {counts.get(i, 0)}/{TARGET_SETS}" for i in START_SIX]
    extra = [f"{names.get(i, i)} {c}" for i, c in sorted(counts.items()) if i not in START_SIX]
    txt = "Postęp nagrań: " + " · ".join(parts)
    if extra:
        txt += "  |  inne: " + " · ".join(extra)
    return txt


def session_label(m: dict) -> str:
    reps = m.get("true_reps", "?")
    return f"{m['day']} {m['file'][:6]} · {m.get('exercise_name', m.get('exercise_id'))} · {m.get('mount')} · {reps} powt. · {m.get('duration_s', 0)} s"


def axis_figure(frames: list[tuple[str, object]], height: int = 1100, window: float | None = None) -> go.Figure:
    fig = make_subplots(rows=len(AXES), cols=1, shared_xaxes=True, vertical_spacing=0.015,
                        subplot_titles=[t for _, t in AXES])
    for k, (name, df) in enumerate(frames):
        color = COLORS[k % len(COLORS)]
        for r, (col, _) in enumerate(AXES, start=1):
            fig.add_trace(go.Scattergl(x=df["t_s"], y=df[col], mode="lines", name=name, legendgroup=name,
                                       showlegend=(r == 1), line={"width": 1.2, "color": color}), row=r, col=1)
    fig.update_layout(height=height, margin={"l": 50, "r": 10, "t": 30, "b": 30}, legend={"orientation": "h", "y": 1.02},
                      uirevision="keep", hovermode="x unified")
    fig.update_xaxes(title_text="t [s]", row=len(AXES), col=1)
    if window is not None and frames:
        tmax = max(float(df["t_s"].iloc[-1]) for _, df in frames if len(df))
        fig.update_xaxes(range=[max(0.0, tmax - window), tmax])
    return fig


app.layout = html.Div(style={"fontFamily": "system-ui, sans-serif", "padding": "0 16px 16px", "background": "#fff", "color": "#111", "minHeight": "100vh"}, children=[
    html.H2("EMOM · rejestrator powtórzeń"),
    html.Div(style={"display": "flex", "gap": "12px", "alignItems": "center", "flexWrap": "wrap"}, children=[
        html.Button("Połącz", id="btn-connect"),
        html.Button("Rozłącz", id="btn-disconnect"),
        html.Span(id="conn-status", style={"fontWeight": "600"}),
        html.Span(id="batt-status"),
        html.Span(id="link-status", style={"color": "#666"}),
    ]),
    dcc.Tabs(id="tabs", value="rec", children=[
        dcc.Tab(label="Nagrywanie", value="rec", children=[
            html.Div(style={"display": "flex", "gap": "12px", "alignItems": "end", "flexWrap": "wrap", "margin": "12px 0"}, children=[
                html.Div([html.Label("Ćwiczenie"), dcc.Dropdown(id="exercise", options=exercise_options(),
                                                               value=EXERCISES[0][0] if EXERCISES else None, clearable=False, style={"width": "360px"})]),
                html.Div([html.Label("Mocowanie"), dcc.Dropdown(id="mount", options=[{"label": n, "value": i} for i, n in MOUNTS],
                                                               value="kettlebell", clearable=False, style={"width": "260px"})]),
                html.Div([html.Label("Orientacja"), dcc.Dropdown(id="orientation", options=[
                    {"label": "USB do góry (uchwyt u góry)", "value": "usb-up"},
                    {"label": "USB w dół (kettlebell dnem do góry)", "value": "usb-down"},
                    {"label": "USB w bok", "value": "usb-side"},
                    {"label": "inna (opisz w uwagach)", "value": "other"}],
                    value="usb-up", clearable=False, style={"width": "300px"})]),
                html.Button("▶ Start serii", id="btn-start", style={"height": "36px", "fontWeight": "700"}),
                html.Button("■ Stop", id="btn-stop", style={"height": "36px"}),
                html.Span(id="rec-status", style={"fontWeight": "600", "color": "#c00"}),
            ]),
            html.Div(id="progress", children=progress_text(), style={"color": "#444", "fontSize": "13px", "margin": "0 0 8px"}),
            html.Div(id="save-form", style={"display": "none", "border": "1px solid #ccc", "padding": "12px", "margin": "8px 0", "borderRadius": "8px"}, children=[
                html.Div(id="save-summary", style={"marginBottom": "8px"}),
                html.Div(style={"display": "flex", "gap": "12px", "alignItems": "end", "flexWrap": "wrap"}, children=[
                    html.Div([html.Label("Faktyczna liczba powtórzeń"), dcc.Input(id="true-reps", type="number", min=0, step=1, style={"width": "120px"})]),
                    html.Div([html.Label("Tempo"), dcc.Dropdown(id="tempo", options=[{"label": t, "value": t} for t in ["normalne", "wolne", "szybkie", "mieszane"]],
                                                               value="normalne", clearable=False, style={"width": "160px"})]),
                    html.Div([html.Label("Uwagi (np. odstawienie, poprawka chwytu)"), dcc.Input(id="notes", type="text", style={"width": "420px"})]),
                    dcc.Checklist(id="dirty", options=[{"label": " brudna seria (celowe zakłócenia)", "value": "dirty"}], value=[], style={"paddingBottom": "6px"}),
                    html.Button("Zapisz", id="btn-save", style={"height": "36px", "fontWeight": "700"}),
                    html.Button("Odrzuć", id="btn-discard", style={"height": "36px"}),
                ]),
                html.Div(id="save-result", style={"marginTop": "8px", "color": "#060"}),
            ]),
            dcc.Graph(id="live-graph", config={"displayModeBar": False}),
        ]),
        dcc.Tab(label="Przeglądanie", value="browse", children=[
            html.Div(style={"display": "flex", "gap": "12px", "alignItems": "end", "margin": "12px 0"}, children=[
                html.Div([html.Label("Sesje (do porównania wybierz kilka)"),
                          dcc.Dropdown(id="sessions", options=[], multi=True, style={"width": "900px"})]),
                html.Button("Odśwież listę", id="btn-refresh"),
            ]),
            html.Div(id="session-meta", style={"whiteSpace": "pre-wrap", "fontFamily": "monospace", "fontSize": "12px"}),
            dcc.Graph(id="browse-graph"),
        ]),
    ]),
    dcc.Interval(id="tick", interval=300, n_intervals=0),
    dcc.Store(id="dummy"),
])


@app.callback(Output("dummy", "data"), Input("btn-connect", "n_clicks"), Input("btn-disconnect", "n_clicks"), prevent_initial_call=True)
def connection_buttons(_c, _d):
    if ctx.triggered_id == "btn-connect":
        STREAM.connect()
    else:
        STREAM.disconnect()
    return time.time()


@app.callback(Output("conn-status", "children"), Output("batt-status", "children"), Output("link-status", "children"),
              Output("rec-status", "children"), Output("live-graph", "figure"), Input("tick", "n_intervals"))
def refresh(_n):
    st = STREAM.state
    labels = {"idle": "rozłączono", "scanning": "szukam EMOM-REP…", "connecting": "łączę…", "connected": "połączono", "error": f"błąd: {STREAM.error}"}
    conn = labels.get(st, st)
    batt = ""
    if STREAM.status:
        s = STREAM.status
        batt = f"bateria {s.vbat_mv/1000:.2f} V{' ⚡' if s.charging else ''}"
    link = f"ramki {STREAM.frames}, zgubione {STREAM.dropped_frames}" if STREAM.frames else ""
    rec = ""
    if REC["active"]:
        rec = f"● NAGRYWAM {time.time() - REC['t0']:.0f} s, próbek {len(STREAM.samples)}"
    # live window: last 10 s
    last = list(itertools.islice(reversed(STREAM.samples), 1000))[::-1]
    df = samples_to_df(last)
    fig = axis_figure([("live", df)], height=900, window=10.0) if len(df) else go.Figure(layout={"height": 900})
    return conn, batt, link, rec, fig


@app.callback(Output("save-form", "style"), Output("save-summary", "children"), Output("save-result", "children"),
              Output("true-reps", "value"), Output("notes", "value"), Output("dirty", "value"),
              Input("btn-start", "n_clicks"), Input("btn-stop", "n_clicks"), Input("btn-save", "n_clicks"), Input("btn-discard", "n_clicks"),
              State("exercise", "value"), State("mount", "value"), State("true-reps", "value"), State("tempo", "value"), State("notes", "value"),
              State("orientation", "value"), State("dirty", "value"),
              prevent_initial_call=True)
def recording_buttons(_s, _x, _sv, _dc, exercise, mount, true_reps, tempo, notes, orientation, dirty):
    hidden, shown = {"display": "none"}, {"display": "block", "border": "1px solid #ccc", "padding": "12px", "margin": "8px 0", "borderRadius": "8px"}
    trig = ctx.triggered_id
    if trig == "btn-start":
        if STREAM.state != "connected":
            return hidden, "", "Najpierw połącz z urządzeniem.", no_update, no_update, no_update
        STREAM.clear()
        STREAM.start_stream()
        REC.update(active=True, t0=time.time(), pending=None)
        return hidden, "", "", None, "", []
    if trig == "btn-stop":
        if not REC["active"]:
            return no_update, no_update, no_update, no_update, no_update, no_update
        STREAM.stop_stream()
        time.sleep(0.4)
        REC.update(active=False, pending=STREAM.snapshot())
        n = len(REC["pending"])
        dur = (REC["pending"][-1].t_ms - REC["pending"][0].t_ms) / 1000 if n > 1 else 0
        name = dict(EXERCISES).get(exercise, exercise)
        return shown, f"{name} · {dict(MOUNTS).get(mount, mount)} · {dur:.1f} s · {n} próbek · zgubione ramki: {STREAM.dropped_frames}", "", None, "", []
    if trig == "btn-save":
        if not REC["pending"]:
            return hidden, "", "Nie ma czego zapisać.", no_update, no_update, no_update
        if true_reps is None:
            return shown, no_update, "Podaj faktyczną liczbę powtórzeń.", no_update, no_update, no_update
        meta = {"exercise_id": exercise, "exercise_name": dict(EXERCISES).get(exercise, exercise), "mount": mount,
                "true_reps": int(true_reps), "tempo": tempo, "notes": notes or "", "orientation": orientation,
                "dirty": bool(dirty), "device": "EMOM-REP",
                "rate_hz": STREAM.status.rate_hz if STREAM.status else None, "dropped_frames": STREAM.dropped_frames,
                "firmware": "stream v1", "person": "TS"}
        path = save_session(REC["pending"], meta)
        REC["pending"] = None
        return hidden, "", f"Zapisano {path.relative_to(path.parents[3])}", None, "", []
    if trig == "btn-discard":
        REC["pending"] = None
        return hidden, "", "Odrzucono.", None, "", []
    return no_update, no_update, no_update, no_update, no_update, no_update


@app.callback(Output("exercise", "options"), Output("progress", "children"), Input("save-result", "children"), prevent_initial_call=True)
def refresh_exercise_marks(_saved):
    return exercise_options(), progress_text()


@app.callback(Output("sessions", "options"), Input("btn-refresh", "n_clicks"), Input("tabs", "value"), Input("save-result", "children"))
def session_options(_r, tab, _saved):
    if tab != "browse" and ctx.triggered_id != "save-result":
        return no_update
    return [{"label": session_label(m), "value": m["path"]} for m in list_sessions()]


@app.callback(Output("browse-graph", "figure"), Output("session-meta", "children"), Input("sessions", "value"))
def browse(paths):
    if not paths:
        return go.Figure(layout={"height": 300}), ""
    metas = {m["path"]: m for m in list_sessions()}
    frames, lines = [], []
    for p in paths:
        m = metas.get(p, {})
        df = load_session(p)
        label = f"{m.get('file', p)[:6]} {m.get('exercise_id', '')} {m.get('true_reps', '?')}p"
        frames.append((label, df))
        lines.append(f"{m.get('day','')} {m.get('file','')}: {m.get('exercise_name','')} · {m.get('mount','')} · {m.get('true_reps','?')} powt. · "
                     f"{m.get('duration_s','')} s · {m.get('samples','')} próbek · tempo {m.get('tempo','')} · zgubione {m.get('dropped_frames','')} · {m.get('notes','')}")
    return axis_figure(frames, height=1200), "\n".join(lines)


def main():
    import logging
    logging.getLogger("werkzeug").setLevel(logging.WARNING)  # hide per-request lines from the terminal
    print("Rejestrator: http://127.0.0.1:8050  (Ctrl-C konczy)")
    app.run(debug=False, host="127.0.0.1", port=8050)
