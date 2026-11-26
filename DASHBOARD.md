# Lovelace Dashboard Strategy & Storage-Mode Analysis

This document details the analysis, architectural approaches, and technical options for managing the Notifier Hub Lovelace dashboard in Home Assistant, specifically addressing feedback from the HACS default store review (PR [#14032](https://github.com/hacs/default/pull/14032)).

---

## 1. Background & Review Feedback

In review feedback for HACS inclusion, maintainer `@frenck` noted:
> *"The dashboard YAML in `/config` gets overwritten. `async_install_dashboard` copies the bundled dashboard to `/config/notifier_hub_dashboard.yaml`, with `install_dashboard` on by default. `async_update_config` and `_handle_set_config` call it with `force=True`. The update listener runs on every options change, and every switch, number and time entity write updates the options. So toggling any Notifier Hub switch overwrites whatever the user changed in that file. Integrations should not write YAML files in the config directory at all. Please drop the automatic copy and let users add the dashboard themselves (you already ship YAML samples and document the steps), or create a storage-mode dashboard through the UI storage APIs. This also takes care of `source.exists()`, which runs on the event loop on that same path."*

---

## 2. Technical Evaluation: Storage-Mode Dashboard Registration

### Can it be done programmatically?
**Yes.** Instead of writing a YAML file to `/config`, Home Assistant supports Lovelace dashboards in **storage mode**, stored internally under `.storage/lovelace.<url_path>` and managed by Home Assistant's UI storage collection APIs.

### How Home Assistant Registers Storage Dashboards

Home Assistant's Lovelace integration exposes a dashboards collection in `hass.data["lovelace"].dashboards`.

A programmatic storage dashboard workflow consists of three steps:

#### Step A: Registering the Dashboard Entry
When a dashboard is created, it must be added to the dashboard collection:
```python
dashboards = hass.data.get("lovelace", {}).dashboards
existing = any(d.url_path == "notifier-hub" for d in dashboards.async_items())

if not existing:
    dashboard_data = {
        "url_path": "notifier-hub",
        "title": "Notifier Hub",
        "icon": "mdi:message-badge",
        "show_in_sidebar": True,
        "require_admin": False,
        "mode": "storage",
    }
    # Persists the dashboard entry in .storage/lovelace_dashboards
    new_dashboard = await dashboards.async_create_item(dashboard_data)
```

#### Step B: Loading & Populating the Card / View Layout
Once registered, the dashboard configuration (views, cards, badges) must be populated:
```python
# Read bundled YAML asynchronously off the event loop
def _read_bundled_yaml(path: str) -> dict:
    import yaml
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

bundled_path = hass.config.path("custom_components/notifier_hub/notifier_hub_dashboard.es.yaml")
dashboard_config = await hass.async_add_executor_job(_read_bundled_yaml, bundled_path)

# Save configuration into the storage dashboard
await new_dashboard.async_save(dashboard_config)
```

#### Step C: Cleanup on Integration Removal
When the config entry is unloaded or removed (`async_remove_entry`):
```python
item = next((d for d in dashboards.async_items() if d.url_path == "notifier-hub"), None)
if item:
    await dashboards.async_delete_item(item.id)
```

---

## 3. Comparison of Approaches

| Criteria | Automated Storage-Mode Registration | Manual User Import (Documentation / Samples) |
| :--- | :--- | :--- |
| **User Experience** | Seamless: dashboard appears in the sidebar automatically. | Simple: user copies YAML into a new manual dashboard. |
| **Compliance with HA Policy** | Allowed, provided no files are written to `/config/` and I/O does not block the loop. | **100% compliant and standard** across the vast majority of HACS custom components. |
| **API Stability & Maintenance** | **High risk**: `hass.data["lovelace"]` is an internal, private, undocumented Home Assistant frontend API. Any upstream HA frontend refactor can break the integration setup. | **Zero risk**: no dependency on internal HA frontend APIs. |
| **User Customization & Updates** | Updating the integration's default layout in future versions without overwriting user-customized cards is complex and prone to conflicts. | Clean: user owns their dashboard and edits freely without risk of programmatic overwrites. |

---

## 4. Recommendations for Notifier Hub

1. **Primary & Recommended Path (for HACS default approval)**:
   - Completely remove the automatic `/config/notifier_hub_dashboard.yaml` copying logic and the `install_dashboard` option.
   - Remove blocking filesystem calls like `source.exists()` on the event loop.
   - Keep the localized dashboard YAML templates (`notifier_hub_dashboard.es.yaml`, `notifier_hub_dashboard.en.yaml`, etc.) in the integration directory as reference examples.
   - Provide clear instructions in the README on how users can create a new dashboard in Home Assistant (via **Settings → Dashboards → Add Dashboard**) and paste the provided YAML template in Raw Configuration mode.

2. **Optional Future Enhancement**:
   - If a one-click dashboard installation button is desired in the future, it should implement the Storage API pattern described in Section 2, wrapped with defensive error handling to ensure HA updates do not impact core notification functionality.
