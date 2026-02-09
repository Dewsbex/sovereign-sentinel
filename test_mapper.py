#!/usr/bin/env python3
"""Test data_mapper components"""

import json
from data_mapper import map_live_state_to_ui_context, load_sniper_candidates

# Test 1: Load live_state
try:
    with open('data/live_state.json', 'r') as f:
        live_state = json.load(f)
    print(f"✅ Loaded live_state: {type(live_state)}")
    print(f"   Keys: {list(live_state.keys())}")
except Exception as e:
    print(f"❌ Failed to load live_state: {e}")

# Test 2: Map to UI context
try:
    context = map_live_state_to_ui_context(live_state)
    print(f"✅ Mapped to context: {len(context)} keys")
    print(f"   Context keys: {list(context.keys())}")
    
    # Check for Undefined objects
    for key, val in context.items():
        val_type = type(val).__name__
        if 'Undefined' in val_type:
            print(f"❌ FOUND UNDEFINED: {key} = {val_type}")
        else:
            print(f"   {key}: {val_type}")
            
except Exception as e:
    print(f"❌ Failed to map context: {e}")
    import traceback
    traceback.print_exc()

# Test 3: JSON serialize the context
try:
    json_str = json.dumps(context, indent=2)
    print(f"✅ Context is JSON serializable ({len(json_str)} chars)")
except Exception as e:
    print(f"❌ Context NOT JSON serializable: {e}")
