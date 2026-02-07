using System;
using BepInEx;
using BepInEx.Logging;
using BepInEx.Configuration;
using HarmonyLib;
using UnityEngine;

namespace NO_GlassScreen.Core {
    [BepInPlugin("NO_GlassScreen", "NOGS", "0.1.0")]
    public class Plugin : BaseUnityPlugin {
        public static Harmony harmony;
        public static ConfigEntry<bool> webServerEnabled;
        public static ConfigEntry<int> webServerPort;
        public static ConfigEntry<float> webSyncInterval;
        public static ConfigEntry<bool> debugModeEnabled;
        internal static new ManualLogSource Logger;
        public static Plugin Instance;

        private void Awake() {
            Instance = this;

            // Web Server settings
            webServerEnabled = Config.Bind("Web Server",
                "Web Server - Enabled",
                true,
                new ConfigDescription(
                    "Enable or disable the Web Bridge sync loop.",
                    null,
                    new ConfigurationManagerAttributes { Order = 2 }));

            webServerPort = Config.Bind("Web Server",
                "Web Server - Port",
                8080,
                new ConfigDescription(
                    "Port the Python NiceGUI server listens on.",
                    null,
                    new ConfigurationManagerAttributes { Order = 1 }));

            webSyncInterval = Config.Bind("Web Server",
                "Web Server - Sync Interval",
                0.5f,
                new ConfigDescription(
                    "Seconds between each sync request to the web server.",
                    null,
                    new ConfigurationManagerAttributes { Order = 0 }));

            // Debug Mode
            debugModeEnabled = Config.Bind("Debug Mode",
                "Debug Mode - Enabled",
                true,
                "Enable or disable the debug mode for logging");

            // Plugin startup logic
            harmony = new Harmony("george.NO_GlassScreen");
            Logger = base.Logger;

            // CORE PATCHES
            if (webServerEnabled.Value) {
                harmony.PatchAll(typeof(NO_GlassScreen.Server.TelemetricsPlugin));
            }

            // Log completion
            Log("NO GlassScreen loaded successfully!");
        }


        public static void Log(string message) {
            if (debugModeEnabled.Value) {
                TimeSpan timeSpan = TimeSpan.FromSeconds(Time.realtimeSinceStartup);
                string formattedTime = string.Format("{0:D2}:{1:D2}:{2:D2}", timeSpan.Hours, timeSpan.Minutes, timeSpan.Seconds);
                Logger.LogInfo("[" + formattedTime + "] " + message);
            }
        }
    }
}
