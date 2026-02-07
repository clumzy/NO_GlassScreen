from nicegui import ui, app
from fastapi import Request

# state and commands
# Current state of the plane systems (synced FROM the game mod)
plane_state: dict[str, bool] = {
    "lights":         False,
    "flight_control": False,
    "radar":          False,
    "night_vision":   False,
    "wheels":         False,
    "engine":         False,
}

# commands waiting to be picked up by the game mod
pending_commands: list[str] = []

ICONS = {
    "lights":         "flare",
    "flight_control": "precision_manufacturing",
    "radar":          "settings_input_antenna",
    "night_vision":   "visibility",
    "wheels":         "radio_button_checked",
    "engine":         "propane_tank",
}


def toggle(key: str):
    """Queue a toggle command — we do NOT flip the UI ourselves.
    The mod will change the in-game state and sync it back to us,
    preventing desync when the game blocks an action."""
    pending_commands.append(key)
    ui.run_javascript("window.navigator.vibrate(50)")


# web ui
@ui.page("/")
def index():
    # VIBE CODED UI SHIT
    ui.query('body').style('background: radial-gradient(circle, #1a1a1a 0%, #000000 100%); color: #e0e0e0; font-family: "Share Tech Mono", monospace; overflow: hidden;')
    ui.add_head_html('''
        <link href="https://fonts.googleapis.com/css2?family=Share+Tech+Mono&display=swap" rel="stylesheet">
        <style>
            @keyframes scan {
                from { top: -20%; }
                to { top: 100%; }
            }
            .scanline {
                position: fixed;
                top: 0; left: 0; width: 100%; height: 5vh;
                background: linear-gradient(to bottom, rgba(255,255,255,0) 0%, rgba(255,255,255,0.03) 50%, rgba(255,255,255,0) 100%);
                animation: scan 4s linear infinite;
                pointer-events: none;
                z-index: 9999;
            }
            .crt-overlay {
                position: fixed; top: 0; left: 0; width: 100%; height: 100%;
                background: linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.1) 50%), linear-gradient(90deg, rgba(255, 0, 0, 0.03), rgba(0, 255, 0, 0.01), rgba(0, 0, 255, 0.03));
                background-size: 100% 2px, 3px 100%;
                pointer-events: none;
                z-index: 9998;
            }
        </style>
    ''')
    
    # CRT Overlays
    ui.element('div').classes('scanline')
    ui.element('div').classes('crt-overlay')

    with ui.column().classes('w-full max-w-lg mx-auto items-center q-pa-md'):
        # CRT-style Header
        with ui.row().classes('w-full justify-between items-end border-b-2 border-green-700 pb-1 mb-8'):
            with ui.column().classes('gap-0'):
                ui.label("NO Glass Screen").classes('text-green-500 text-4xl font-black italic tracking-tighter leading-none')
                ui.label("This post was made by \"George\" Gang").classes('text-green-900 text-[8px] font-bold tracking-[0.3em]')
            with ui.column().classes('items-end gap-0'):
                ui.label("LINK: ONLINE").classes('text-green-500 text-[10px] font-bold')
                ui.label("SYS: 0.1.0").classes('text-green-900 text-[10px]')

        # Control Grid
        with ui.grid(columns=2).classes('w-full gap-6'):
            for key in plane_state:
                icon_name = ICONS.get(key, 'settings')
                display_name = key.replace('_', ' ').upper()
                
                with ui.card().tight().classes('bg-transparent border-0 shadow-none'):
                    btn = ui.button(on_click=lambda _, k=key: toggle(k)).classes('w-full h-48 flex flex-col p-4 border-2 transition-all duration-300 rounded-lg bg-black text-green-500 border-green-500').props('unelevated stack')
                    with btn:
                        icon = ui.icon(icon_name).classes('text-7xl mb-auto mt-2')
                        ui.label(display_name).classes('text-[10px] font-black tracking-widest mt-4 opacity-50')
                        status_label = ui.label().classes('text-2xl font-black tracking-widest')
                    
                    # Reactive UI Updates
                    def update_ui(val, b=btn, sl=status_label, ic=icon):
                        if val:
                            # ON STYLE: Solid Green Background, White Content
                            b.style('background-color: #22c55e !important; color: #ffffff !important; border-color: #22c55e !important;')
                            b.classes('shadow-[0_0_30px_rgba(34,197,94,0.4)]')
                            ic.style('color: #ffffff !important;')
                            sl.text = "ACTIVE"
                        else:
                            # OFF STYLE: Black Background, Green Outline/Icon
                            b.style('background-color: #000000 !important; color: #22c55e !important; border-color: #22c55e !important;')
                            b.classes(remove='shadow-[0_0_30px_rgba(34,197,94,0.4)]')
                            ic.style('color: #22c55e !important;')
                            sl.text = "OFF"
                    
                    # Trigger UI update side effect
                    ui.label().bind_visibility_from(plane_state, key, backward=lambda v, f=update_ui: (f(v), False)[1])

        # Bottom Telemetry Bar
        with ui.row().classes('w-full mt-12 justify-between items-center opacity-30 border-t border-slate-800 pt-4'):
            ui.label("SYNC: 60FPS").classes('text-[10px] uppercase')
            ui.label("ESTABLISHED CONNECTION").classes('text-[10px] uppercase animate-pulse')
            ui.label("NO-TEK HUD SYS").classes('text-[10px] uppercase')


# api for game mod to sync state and receive commands
@app.post("/sync")
async def sync(request: Request):
    """Called by the C# mod every ~0.5 s.
    - Receives the real game state as JSON  → updates our UI dict
    - Returns any queued toggle commands  → mod executes them in-game
    """
    global plane_state, pending_commands

    data = await request.json()
    plane_state.update(data)  # merge real game state into our UI

    commands_to_send = list(pending_commands)
    pending_commands.clear()
    return {"commands": commands_to_send}


# script entry point
if __name__ in {"__main__", "__mp_main__"}:
    ui.run(host="0.0.0.0", port=8080, title="NO Tactical", reload=False)
