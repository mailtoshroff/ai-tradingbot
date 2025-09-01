#!/usr/bin/env python3
"""
Simplified bot test to identify where it gets stuck
"""
import asyncio
import sys
import os
import time

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def test_simple_bot():
    """Test the bot step by step to identify the issue"""
    print("🚀 Simple Bot Test - Step by Step")
    print("=" * 50)
    
    try:
        # Step 1: Import and create bot
        print("1. Creating bot instance...")
        from main import AITradingBot
        bot = AITradingBot()
        print("   ✅ Bot instance created")
        
        # Step 2: Test initialization
        print("\n2. Testing initialization...")
        start_time = time.time()
        init_success = await bot.initialize()
        init_time = time.time() - start_time
        
        if init_success:
            print(f"   ✅ Initialization successful in {init_time:.2f}s")
        else:
            print("   ❌ Initialization failed")
            return False
        
        # Step 3: Test single run
        print("\n3. Testing single run...")
        start_time = time.time()
        run_success = await bot.run_once()
        run_time = time.time() - start_time
        
        if run_success:
            print(f"   ✅ Single run successful in {run_time:.2f}s")
        else:
            print("   ❌ Single run failed")
            return False
        
        print("\n🎉 Bot test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Bot test error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function"""
    try:
        return asyncio.run(test_simple_bot())
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
