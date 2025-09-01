#!/usr/bin/env python3
"""
Test script for main bot execution
"""
import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def test_main_execution():
    """Test the main bot execution"""
    print("🚀 Testing Main Bot Execution")
    print("=" * 50)
    
    try:
        from main import main
        
        print("Starting main bot execution...")
        start_time = asyncio.get_event_loop().time()
        
        # Run the main function
        result = await main()
        
        end_time = asyncio.get_event_loop().time()
        exec_time = end_time - start_time
        
        print(f"✅ Main execution completed in {exec_time:.2f}s")
        print(f"Result: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Main execution error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main_sync():
    """Synchronous wrapper for the async test"""
    return asyncio.run(test_main_execution())

if __name__ == "__main__":
    success = main_sync()
    sys.exit(0 if success else 1)
