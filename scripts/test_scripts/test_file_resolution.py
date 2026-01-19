"""
Test File Resolution Standalone Script

This script tests the file resolution logic independently to debug
why files aren't being found.
"""

import os
import sys

# Add repo to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../repo"))

from app.services.file_resolver import FileResolver

def test_file_resolution():
    """Test file resolution with actual parameters."""
    
    print("="*80)
    print("FILE RESOLUTION TEST")
    print("="*80)
    
    # Parameters from the routing result
    client_name = "CEP"
    wave_number = "6"
    
    # Base path
    base_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../OPN-Agent/AI_open_negotiation/Data/Input")
    )
    
    print(f"\n📂 Base Path: {base_path}")
    print(f"   Exists: {os.path.exists(base_path)}")
    
    if os.path.exists(base_path):
        print(f"\n📄 Files in directory:")
        for file in os.listdir(base_path):
            print(f"   - {file}")
    
    # Patterns to test
    patterns = {
        "excel": "{client_name} W{wave_number}*.xlsx",
        "template": "*Template*.docx"
    }
    
    print(f"\n🔍 Patterns:")
    for key, pattern in patterns.items():
        formatted = pattern.format(client_name=client_name, wave_number=wave_number)
        print(f"   {key}: {pattern} -> {formatted}")
    
    # Test resolution
    print(f"\n⚙️  Testing FileResolver...")
    try:
        resolver = FileResolver(base_path)
        resolved = resolver.resolve_files(
            client_name=client_name,
            wave_number=wave_number,
            patterns=patterns
        )
        
        print(f"\n✅ Resolution Result:")
        if resolved:
            for file_type, path in resolved.items():
                if path:
                    print(f"   ✓ {file_type}: {path}")
                    print(f"     Exists: {os.path.exists(path)}")
                else:
                    print(f"   ✗ {file_type}: NOT FOUND")
        else:
            print(f"   ❌ No files resolved (empty dict)")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_file_resolution()
