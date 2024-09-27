lehigh4mgs test files (used within microgridPlan for PowerModelsONM and ProtectionSettingsOptimizer) :

- circuit_plus_mgAll_relays.dss : 8760-element loadshapes
- circuit_plus_mgAll_relays_new.dss : 24-element loadshapes
    - runs with ProtectionSettingsOptimizer successfully (29 second runtime)
    - errors for PowerModelsONM
- circuit_plus_mgAll_relays_df.dss : 24-element loadshapes
    - version edited by David Fobes (from circuit_plus_mgAll_relays_new.dss)
    - runs with PowerModelsONM successfully (5:04 minute runtime)
    - runs with ProtectionSettingsOptimizier but doesn't produce fitness results (21:09 minute runtime)

- circuit_plus_mgAll_relays.events.json
    - currenly used for PowerModelsONM
- circuit_plus_mgAll_relays.settings.json
    - currently used for PowerModelsONM