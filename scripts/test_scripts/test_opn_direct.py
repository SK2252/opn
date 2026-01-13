"""
Direct test of OPN-Agent document generation.
Tests the orchestrator agent directly without HTTP layer.
"""
import asyncio
import os
import sys

# Add OPN-Agent to path
sys.path.insert(0, "D:/opn/yak_tech/OPN-Agent")

os.environ["PYTHONPATH"] = "D:/opn/yak_tech/OPN-Agent"

from AI_open_negotiation.agents.document_agent.orchestrator_agent import OrchestratorAgent

async def test_direct():
    print("=" * 60)
    print("DIRECT OPN-AGENT TEST")
    print("=" * 60)
    
    # Config for document generation
    config = {
        "excel_path": "D:/opn/yak_tech/OPN-Agent/AI_open_negotiation/Data/Input/CEP W6 OPNNEG TEMPLATE.xlsx",
        "template_docx": "D:/opn/yak_tech/OPN-Agent/AI_open_negotiation/Data/Input/OpenNeg_CEP_Template.docx",
        "output_group_folder": "D:/opn/yak_tech/OPN-Agent/AI_open_negotiation/Data/Output/CEP_W6/groups",
        "output_notice_folder": "D:/opn/yak_tech/OPN-Agent/AI_open_negotiation/Data/Output/CEP_W6/notices",
        "merged_output_folder": "D:/opn/yak_tech/OPN-Agent/AI_open_negotiation/Data/Output/CEP_W6/merged",
    }
    
    print("\n📂 Input files:")
    print(f"   Excel: {config['excel_path']}")
    print(f"   Template: {config['template_docx']}")
    print(f"\n📁 Output folder: {config['merged_output_folder']}")
    
    # Check input files exist
    if not os.path.exists(config["excel_path"]):
        print(f"\n❌ Excel file not found: {config['excel_path']}")
        return
    
    if not os.path.exists(config["template_docx"]):
        print(f"\n❌ Template file not found: {config['template_docx']}")
        return
    
    print("\n✅ Input files verified")
    
    # Create orchestrator and process
    print("\n🔄 Starting document generation...")
    orchestrator = OrchestratorAgent({"max_retries": 3})
    
    try:
        result = await orchestrator.process_document_request(config)
        
        print(f"\n📊 Result Status: {result.get('status')}")
        
        if result.get("stats"):
            stats = result["stats"]
            print(f"   Total Records: {stats.get('total_records', 'N/A')}")
            print(f"   Successful: {stats.get('successful', 'N/A')}")
            print(f"   Failed: {stats.get('failed', 'N/A')}")
        
        if result.get("errors"):
            print(f"\n⚠️  Errors: {result['errors']}")
        
        if result.get("warnings"):
            print(f"\n⚠️  Warnings: {result['warnings']}")
        
        # Check output folder
        output_folder = config["merged_output_folder"]
        if os.path.exists(output_folder):
            files = os.listdir(output_folder)
            print(f"\n📂 Output folder contents ({len(files)} files):")
            for f in files[:10]:
                print(f"   - {f}")
            if len(files) > 10:
                print(f"   ... and {len(files) - 10} more")
        else:
            print(f"\n❌ Output folder not created: {output_folder}")
        
        return result
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    result = asyncio.run(test_direct())
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)
