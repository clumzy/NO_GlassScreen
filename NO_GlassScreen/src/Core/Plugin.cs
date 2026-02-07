using System;
using BepInEx;
using BepInEx.Logging;
using BepInEx.Configuration;
using HarmonyLib;
using UnityEngine;

namespace NO_GlassScreen.Core {
    [BepInPlugin("NO_GlassScreen", "NOTT", "0.6.0.2")]
    public class Plugin : BaseUnityPlugin {
        public static Harmony harmony;
        public static ConfigEntry<string> webServerEnabled;
        public static ConfigEntry<bool> debugModeEnabled;
        internal static new ManualLogSource Logger;
        public static Plugin Instance;

        private void Awake() {
            Instance = this;
            // MFD Nav
            webServerEnabled = Config.Bind("Web Server",
                "Web Server - Enabled",
                "",
                new ConfigDescription(
                    "Enable or disable the Web Server.",
                    null,
                    new ConfigurationManagerAttributes {
                        Order = 0
                    }));
            // Debug Mode settings
            debugModeEnabled = Config.Bind("Debug Mode",
                "Debug Mode - Enabled",
                true,
                "Enable or disable the debug mode for logging");
            // Plugin startup logic
            harmony = new Harmony("george.NO_GlassScreen");
            Logger = base.Logger;
            // CORE PATCHES
            //harmony.PatchAll(typeof(RegisterControllerPatch));
            // Log completion
            Log("NO GlassScreen loaded successfully !");
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
