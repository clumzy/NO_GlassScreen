using System;
using BepInEx.Configuration;
using UnityEngine;
using Rewired;
using HarmonyLib;
using System.Collections;
using System.Linq;

namespace NO_GlassScreen.Core;

internal sealed class ConfigurationManagerAttributes
/// <summary>
/// Class that can be used to customize how a setting is displayed in the configuration manager window.
/// </summary>
{
    public bool? IsAdvanced;
    public bool? Browsable;
    public string Category;
    public Action<ConfigEntryBase> CustomDrawer;
    public string DispName;
    public int? Order;
    public bool? ReadOnly;
    public bool? HideDefaultButton;
    public bool? HideSettingName;
    public object ControllerName;
    public object ButtonIndex;
}