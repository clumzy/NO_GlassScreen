using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Text;
using UnityEngine;
using NO_GlassScreen.Core;

namespace NO_GlassScreen.Server {
    public static class WebBridge {
        // network stuff
        private static readonly HttpClient httpClient = new();
        private static float nextSyncTime = 0f;
        private static bool running = false;

        // config
        public static string ServerUrl => $"http://localhost:{Plugin.webServerPort.Value.ToString()}/sync";
        public static float SyncIntervalSeconds => Plugin.webSyncInterval.Value;

        // api
        public static void Start() {
            running = true;
            nextSyncTime = 0f;
            Plugin.Log("[WebBridge] Sync started.");
        }

        public static void Stop() {
            running = false;
            Plugin.Log("[WebBridge] Sync stopped.");
        }

        public static void Tick() {
            if (!running) return;
            if (Time.time < nextSyncTime) return;
            nextSyncTime = Time.time + SyncIntervalSeconds;

            var state = ReadGameState();
            SendSync(state);
        }

        // data wrapperr
        [Serializable]
        private class GameState {
            public bool lights;
            public bool flight_control;
            public bool radar;
            public bool night_vision;
            public bool wheels;
            public bool engine;
            public string mfd_main_color;
            public string mfd_text_color;
            public string weapon_name;
            public string weapon_ammo;
            public int ir_flare;
            public int ir_flare_max;
            public int ew_jammer;
        }

        [Serializable]
        private class SyncResponse {
            public List<string> commands;
        }
        private static GameState ReadGameState() {
            return new GameState {
                lights         = ReadLights(),
                flight_control = ReadFlightControl(),
                radar          = ReadRadar(),
                night_vision   = ReadNightVision(),
                wheels         = ReadWheels(),
                engine         = ReadEngine(),
                mfd_main_color = ReadMFDMainColor(),
                mfd_text_color = ReadMFDTextColor(),
                weapon_name    = ReadWeaponName(),
                weapon_ammo    = ReadWeaponAmmo(),
                ir_flare       = ReadIRFlare(),
                ir_flare_max   = ReadIRFlareMax(),
                ew_jammer      = ReadEWJammer(),
            };
        }

        private static string ReadMFDMainColor() {
            return GetNOTTColor(ref _nottMainColorField, "otherComponentMainColor", "#22c55e");
        }

        private static string ReadMFDTextColor() {
            return GetNOTTColor(ref _nottTextColorField, "otherComponentTextColor", "#22c55e");
        }

        private static System.Reflection.FieldInfo _nottMainColorField = null;
        private static System.Reflection.FieldInfo _nottTextColorField = null;
        private static bool _nottSearched = false;

        private static string GetNOTTColor(ref System.Reflection.FieldInfo fieldCache, string fieldName, string defaultHex) {
            try {
                if (!_nottSearched && fieldCache == null) {
                    foreach (var assembly in AppDomain.CurrentDomain.GetAssemblies()) {
                        if (assembly.GetName().Name == "NO_Tactitools") {
                            var type = assembly.GetType("NO_Tactitools.UI.MFD.MFDColorComponent+InternalState");
                            if (type != null) {
                                _nottMainColorField = type.GetField("otherComponentMainColor", System.Reflection.BindingFlags.Static | System.Reflection.BindingFlags.Public | System.Reflection.BindingFlags.NonPublic);
                                _nottTextColorField = type.GetField("otherComponentTextColor", System.Reflection.BindingFlags.Static | System.Reflection.BindingFlags.Public | System.Reflection.BindingFlags.NonPublic);
                            }
                            break;
                        }
                    }
                    _nottSearched = true;
                }

                if (fieldCache != null) {
                    Color color = (Color)fieldCache.GetValue(null);
                    return "#" + ColorUtility.ToHtmlStringRGB(color);
                }
            } catch (Exception) {
                // Return default on error
            }
            return defaultHex;
        }

        private static TraverseCache<Aircraft, NavLights> _navLightsCache = new("navLights");
        private static TraverseCache<NavLights, bool> _navLightsOnCache = new("isOn");

        private static bool ReadLights() {
            return _navLightsOnCache.GetValue(_navLightsCache.GetValue(GameBindings.Player.Aircraft.GetAircraft()));
        }

        private static bool ReadFlightControl() {
            return GameBindings.Player.Aircraft.GetAircraft()?.flightAssist ?? false;
        }

        private static bool ReadRadar() {
            try {
                return GameBindings.Player.Aircraft.GetAircraft()?.radar.activated ?? false;
            }
            catch (Exception) {
                // in case radar is not installed, return false
                return false;
            }
        }

        private static TraverseCache<NightVision, bool> _nightVisionCache = new("nightVisActive");
        private static bool ReadNightVision() {
            return _nightVisionCache.GetValue(NightVision.i);
        }

        private static bool ReadWheels() {
            return GameBindings.Player.Aircraft.GetAircraft()?.gearDeployed ?? false;
        }

        private static bool ReadEngine() {
            return GameBindings.Player.Aircraft.GetAircraft()?.Ignition ?? false;
        }

        private static string ReadWeaponName() {
            try {
                return GameBindings.Player.Aircraft.Weapons.GetActiveStationName() ?? "NONE";
            }
            catch (Exception) {
                return "NONE";
            }
        }

        private static string ReadWeaponAmmo() {
            try {
                string ammoStr = GameBindings.Player.Aircraft.Weapons.GetActiveStationAmmoString();
                return ammoStr?.Replace(" ", "") ?? "0";
            }
            catch (Exception) {
                return "0";
            }
        }

        private static int ReadIRFlare() {
            try {
                return GameBindings.Player.Aircraft.Countermeasures.GetIRFlareAmmo();
            }
            catch (Exception) {
                return 0;
            }
        }

        private static int ReadIRFlareMax() {
            try {
                return GameBindings.Player.Aircraft.Countermeasures.GetIRFlareMaxAmmo();
            }
            catch (Exception) {
                return 128; // fallback to default max
            }
        }

        private static int ReadEWJammer() {
            try {
                return GameBindings.Player.Aircraft.Countermeasures.GetJammerAmmo();
            }
            catch (Exception) {
                return 0;
            }
        }

        // commands, received from server and executed in-game
        private static void ExecuteCommand(string command) {
            Plugin.Log("[WebBridge] Executing command: "+command.ToString());

            switch (command) {
                case "lights":         ToggleLights();        break;
                case "flight_control": ToggleFlightControl(); break;
                case "radar":          ToggleRadar();         break;
                case "night_vision":   ToggleNightVision();   break;
                case "wheels":         ToggleWheels();        break;
                case "engine":         ToggleEngine();        break;
                default:
                    Plugin.Log($"[WebBridge] Unknown command: "+command.ToString());
                    break;
            }
        }

        private static void ToggleLights() {
            GameBindings.Player.Aircraft.GetAircraft()?.ToggleNavLights();
            Plugin.Log("[WebBridge] ToggleLights()");
        }

        private static void ToggleFlightControl() {
            GameBindings.Player.Aircraft.GetAircraft()?.TogglePitchLimiter();
            Plugin.Log("[WebBridge] ToggleFlightControl()");
        }

        private static void ToggleRadar() {
            try {
                GameBindings.Player.Aircraft.GetAircraft()?.CmdToggleRadar();
            }
            catch (Exception) {
                Plugin.Log("[WebBridge] ToggleRadar() failed - radar may not be installed.");
            }
            Plugin.Log("[WebBridge] ToggleRadar()");
        }

        private static void ToggleNightVision() {
            NightVision.Toggle();
            Plugin.Log("[WebBridge] ToggleNightVision()");
        }

        private static void ToggleWheels() {
            GameBindings.Player.Aircraft.GetAircraft()?.SetGear((!GameBindings.Player.Aircraft.GetAircraft()?.gearDeployed) ?? false);
            Plugin.Log("[WebBridge] ToggleWheels()");
        }

        private static void ToggleEngine() {
            GameBindings.Player.Aircraft.GetAircraft()?.CmdToggleIgnition();
            Plugin.Log("[WebBridge] ToggleEngine()");
        }

        // communication function

        private static async void SendSync(GameState state) {
            try {
                string json = JsonUtility.ToJson(state);
                var content = new StringContent(json, Encoding.UTF8, "application/json");

                HttpResponseMessage response = await httpClient.PostAsync(ServerUrl, content);

                if (response.IsSuccessStatusCode) {
                    string body = await response.Content.ReadAsStringAsync();
                    var result = JsonUtility.FromJson<SyncResponse>(body);

                    if (result?.commands != null) {
                        foreach (string cmd in result.commands) {
                            ExecuteCommand(cmd);
                        }
                    }
                }
            }
            catch (HttpRequestException) {
                // server not running, ignore
            }
            catch (Exception ex) {
                Plugin.Log($"[WebBridge] Sync error: "+ex.Message.ToString());
            }
        }
    }
}
