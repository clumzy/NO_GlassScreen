using HarmonyLib;
using NO_GlassScreen.Core;

namespace NO_GlassScreen.Server;

[HarmonyPatch(typeof(MainMenu), "Start")]
class TelemetricsPlugin {
    private static bool initialized = false;
    static void Postfix() {
        if (!initialized) {
            Plugin.Log("[WH] Web Hook plugin starting!");
            // APPLY SUB PATCHES
            Plugin.harmony.PatchAll(typeof(FlightStartTask));
            Plugin.harmony.PatchAll(typeof(FlightResetTask));
            initialized = true;
            Plugin.Log("[WH] Web Hook plugin successfully started!");
        }
    }
}

[HarmonyPatch(typeof(CombatHUD), "FixedUpdate")]
class FlightStartTask {
    static void Postfix() {
        WebBridge.Tick();
    }
}

[HarmonyPatch(typeof(TacScreen), "Initialize")]
class FlightResetTask {
    static void Postfix() {
        WebBridge.Start();
    }
}

