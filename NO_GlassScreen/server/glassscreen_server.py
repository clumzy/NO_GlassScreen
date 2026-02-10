from nicegui import ui, app
from fastapi import Request
import time

# state and commands
# Current state of the plane systems (synced FROM the game mod)
plane_state: dict = {
    "lights":         False,
    "flight_control": False,
    "radar":          False,
    "night_vision":   False,
    "wheels":         False,
    "engine":         False,
    "mfd_main_color": "#22c55e",
    "mfd_text_color": "#22c55e",
}

# commands waiting to be picked up by the game mod
pending_commands: list[str] = []
last_sync: float = 0.0

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


def check_connection_timeout():
    if time.time() - last_sync > 2.0:
        for key in plane_state:
            plane_state[key] = False


# web ui
@ui.page("/")
def index():
    ui.timer(1.0, check_connection_timeout)
    # VIBE CODED UI SHIT
    ui.query('body').style('background: #000000; color: #e0e0e0; font-family: "Orbitron", sans-serif; overflow: hidden;')
    ui.add_head_html('''
        <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&display=swap" rel="stylesheet">
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

    ui.query('body').style('display: flex; flex-direction: column; height: 100vh;')
    
    with ui.column().classes('w-full h-full mx-auto flex flex-col q-pa-md'):
        # Minimalist Header
        header_container = ui.row().classes('w-full justify-between items-center pb-2 mb-6 border-b border-slate-700')
        with header_container:
            title_label = ui.label("NO GLASS").classes('text-2xl font-black tracking-tighter')
            sys_label = ui.label("SYS: 0.1.0").classes('text-[8px] opacity-40 tracking-widest')

        def update_header_styles():
            main_color = plane_state.get('mfd_main_color', '#22c55e')
            header_container.style(f'border-bottom-color: {main_color}; opacity: 0.8;')
            title_label.style(f'color: {main_color}')
            sys_label.style(f'color: {main_color}; opacity: 0.4;')
        
        ui.timer(0.5, update_header_styles)

        # Control Grid - Responsive Flex Layout
        with ui.element('div').classes('w-full flex-grow') as grid_container:
            grid_container.style('display: grid; grid-template-columns: repeat(2, 1fr); grid-auto-rows: 1fr; gap: 0.5rem;')
            
            for key in ["lights", "flight_control", "radar", "night_vision", "wheels", "engine"]:
                icon_name = ICONS.get(key, 'settings')
                display_name = key.replace('_', ' ').upper()
                
                with ui.card().tight().classes('bg-transparent border-0 shadow-none'):
                    btn = ui.button(on_click=lambda _, k=key: toggle(k)).classes('w-full h-full flex flex-row items-center justify-start p-2 transition-all duration-300 bg-black box-border gap-2').props('unelevated stack')
                    btn.style('border: 3px solid currentColor;')
                    with btn:
                        icon = ui.icon(icon_name).classes('text-5xl flex-shrink-0')
                        status_label = ui.label().classes('hidden')
                        ui.label(display_name).classes('text-[10px] font-bold tracking-widest opacity-40 flex-wrap break-words')
                    
                    # Reactive UI Updates
                    def update_ui(ignored_val, k=key, b=btn, sl=status_label, ic=icon):
                        val = plane_state[k]
                        main_color = plane_state.get('mfd_main_color', '#22c55e')
                        
                        if val:
                            # ON STYLE: Solid Main Color Background, White Content
                            b.style(f'background-color: {main_color} !important; color: #ffffff !important; border-color: {main_color} !important;')
                            b.style(f'box-shadow: 0 0 30px {main_color}66;')
                            ic.style('color: #ffffff !important;')
                        else:
                            # OFF STYLE: Black Background, Main Color Outline/Icon
                            b.style(f'background-color: #000000 !important; color: {main_color} !important; border-color: {main_color} !important;')
                            b.style('box-shadow: none;')
                            ic.style(f'color: {main_color} !important;')
                    
                    # Trigger UI update on state OR color change
                    ui.label().bind_visibility_from(plane_state, key, backward=lambda v, f=update_ui: (f(v), False)[1])
                    ui.label().bind_visibility_from(plane_state, 'mfd_main_color', backward=lambda v, f=update_ui: (f(v), False)[1])

        # Bottom Telemetry Bar
        with ui.row().classes('w-full mt-8 justify-center items-center opacity-30 border-t border-slate-800 pt-2'):
            connection_status = ui.label("SEARCHING FOR LINK...").classes('text-[8px] uppercase tracking-widest animate-pulse')

            def update_bottom_bar():
                is_online = time.time() - last_sync < 2.0
                connection_status.text = "LINK ESTABLISHED" if is_online else "LINK OFFLINE"
                
                main_color = plane_state.get('mfd_main_color', '#22c55e')
                connection_status.style(f'color: {main_color}')
            
            ui.timer(1.0, update_bottom_bar)


# api for game mod to sync state and receive commands
@app.post("/sync")
async def sync(request: Request):
    """Called by the C# mod every ~0.5 s.
    - Receives the real game state as JSON  → updates our UI dict
    - Returns any queued toggle commands  → mod executes them in-game
    """
    global plane_state, pending_commands, last_sync

    data = await request.json()
    plane_state.update(data)  # merge real game state into our UI
    last_sync = time.time()

    commands_to_send = list(pending_commands)
    pending_commands.clear()
    return {"commands": commands_to_send}


# script entry point
if __name__ in {"__main__", "__mp_main__"}:
    ui.run(host="0.0.0.0", port=8080, title="NO Tactical", reload=False)
