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
    "weapon_name":    "",
    "weapon_ammo":    "0",
    "ir_flare":       0,
    "ir_flare_max":   128,
    "ew_jammer":      0,
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
                        name_label = ui.label(display_name).classes('text-[10px] font-bold tracking-widest flex-wrap break-words')
                        name_label.style('opacity: 0.4;')
                    
                    # Reactive UI Updates
                    def update_ui(ignored_val, k=key, b=btn, sl=status_label, ic=icon, nl=name_label):
                        val = plane_state[k]
                        main_color = plane_state.get('mfd_main_color', '#22c55e')
                        
                        if val:
                            # ON STYLE: Solid Main Color Background, White Content
                            b.style(f'background-color: {main_color} !important; color: #ffffff !important; border-color: {main_color} !important;')
                            b.style(f'box-shadow: 0 0 30px {main_color}66;')
                            ic.style('color: #ffffff !important;')
                            nl.style('color: #ffffff !important; opacity: 1 !important;')
                        else:
                            # OFF STYLE: Black Background, Main Color Outline/Icon
                            b.style(f'background-color: #000000 !important; color: {main_color} !important; border-color: {main_color} !important;')
                            b.style('box-shadow: none;')
                            ic.style(f'color: {main_color} !important;')
                            nl.style(f'color: {main_color} !important; opacity: 0.4 !important;')
                    
                    # Trigger UI update on state OR color change
                    ui.label().bind_visibility_from(plane_state, key, backward=lambda v, f=update_ui: (f(v), False)[1])
                    ui.label().bind_visibility_from(plane_state, 'mfd_main_color', backward=lambda v, f=update_ui: (f(v), False)[1])

        # Weapon/Countermeasure Display Panel
        with ui.column().classes('w-full flex-grow border-t border-slate-700 pt-4 gap-4'):
            # WEAPONS Section Title
            title_weapons = ui.label("WEAPONS").classes('text-sm font-bold tracking-widest w-full text-center')
            title_weapons.style('opacity: 0.6; letter-spacing: 0.15em;')
            
            # Weapon Display - Full Width
            with ui.row().classes('w-full justify-center items-center'):
                with ui.column().classes('items-center gap-0 flex-grow'):
                    weapon_name_label = ui.label(plane_state.get('weapon_name', 'NONE')).classes('text-2xl font-bold tracking-widest')
                    weapon_name_label.style('color: #ffffff')
                    weapon_ammo_label = ui.label(plane_state.get('weapon_ammo', '0')).classes('text-5xl font-black tracking-widest')
                    weapon_ammo_label.style('color: #ffffff')
            
            # Line between sections
            ui.element('div').classes('w-full border-b border-slate-700')
            
            # COUNTERMEASURES Section Title
            title_cm = ui.label("COUNTERMEASURES").classes('text-sm font-bold tracking-widest w-full text-center')
            title_cm.style('opacity: 0.6; letter-spacing: 0.15em;')
            
            # IR/EW Row - Shared
            with ui.row().classes('w-full justify-center items-center gap-5 flex-grow'):
                # IR Flare Display
                with ui.column().classes('items-center gap-0 flex-grow'):
                    ui.label("IR").classes('text-sm font-bold tracking-widest opacity-40')
                    ir_label = ui.label(str(plane_state.get('ir_flare', 0))).classes('text-4xl font-black tracking-widest')
                    ir_label.style('color: #ffffff')
                
                # EW Jammer Display
                with ui.column().classes('items-center gap-0 flex-grow'):
                    ui.label("EW").classes('text-sm font-bold tracking-widest opacity-40')
                    ew_label = ui.label(f"{plane_state.get('ew_jammer', 0)}%").classes('text-4xl font-black tracking-widest')
                    ew_label.style('color: #ffffff')
            
            def lerp_color(main_color_hex: str, ammo_ratio: float) -> str:
                """Lerp between red (0) and main color (1)"""
                # Ensure we have a valid hex string
                if not isinstance(main_color_hex, str) or not main_color_hex.startswith('#'):
                    main_color_hex = '#22c55e'
                
                try:
                    # Convert hex to RGB
                    main_r = int(main_color_hex[1:3], 16)
                    main_g = int(main_color_hex[3:5], 16)
                    main_b = int(main_color_hex[5:7], 16)
                except (ValueError, IndexError):
                    return '#22c55e'
                
                # Lerp from red (255, 0, 0) to main color
                r = int(255 + (main_r - 255) * ammo_ratio)
                g = int(0 + (main_g - 0) * ammo_ratio)
                b = int(0 + (main_b - 0) * ammo_ratio)
                
                return f'#{r:02x}{g:02x}{b:02x}'
            
            def update_weapon_display():
                # Validate and get main color - ensure it's a string hex value
                main_color = plane_state.get('mfd_main_color', '#22c55e')
                if not isinstance(main_color, str) or not main_color.startswith('#'):
                    main_color = '#22c55e'
                
                weapon_name = str(plane_state.get('weapon_name', 'NONE'))
                weapon_ammo = str(plane_state.get('weapon_ammo', '0'))
                ir_ammo = plane_state.get('ir_flare', 0)
                ir_max = plane_state.get('ir_flare_max', 128)
                ew_ammo = plane_state.get('ew_jammer', 0)
                
                weapon_name_label.text = weapon_name
                weapon_ammo_label.text = weapon_ammo
                ir_label.text = str(ir_ammo)
                ew_label.text = f"{ew_ammo}%"
                
                # Weapon name - white if "False", else main color
                if weapon_name == 'False':
                    weapon_name_label.style('color: #ffffff')
                else:
                    weapon_name_label.style(f'color: {main_color}')
                
                # Weapon ammo - red if out of ammo (0) or "False", else main color
                if weapon_ammo == '0' or weapon_ammo == 'False':
                    weapon_color = '#ffffff' if weapon_ammo == 'False' else '#ff0000'
                else:
                    weapon_color = main_color
                weapon_ammo_label.style(f'color: {weapon_color}')
                
                # IR flare - white if "False", else lerp from red to main color based on ir_flare_max
                if str(ir_ammo) == 'False':
                    ir_label.style('color: #ffffff')
                else:
                    ir_ratio = min(max(ir_ammo, 0) / max(ir_max, 1), 1.0)
                    ir_color = lerp_color(main_color, ir_ratio)
                    ir_label.style(f'color: {ir_color}')
                
                # EW jammer - white if "False", else lerp from red to main color
                if str(ew_ammo) == 'False':
                    ew_label.style('color: #ffffff')
                else:
                    ew_ratio = min(max(ew_ammo, 0) / 100.0, 1.0)
                    ew_color = lerp_color(main_color, ew_ratio)
                    ew_label.style(f'color: {ew_color}')
            
            ui.timer(0.5, update_weapon_display)

        # Bottom Telemetry Bar
        with ui.row().classes('w-full justify-center items-center opacity-30 border-t border-slate-800 pt-2'):
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
