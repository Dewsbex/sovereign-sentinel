
try:
    import generate_static
    print("Import successful")
    if hasattr(generate_static, 'safe_float'):
        print("safe_float found")
    else:
        print("safe_float NOT found")
    
    if hasattr(generate_static, 'main'):
        print("main found")
except Exception as e:
    print(f"Import failed: {e}")
