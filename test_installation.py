#!/usr/bin/env python3
"""
Test script to verify AI Trading Bot installation and basic functionality
"""
import sys
import os
from pathlib import Path

def test_imports():
    """Test if all required modules can be imported"""
    print("🔍 Testing module imports...")
    
    try:
        # Test core imports
        from src.utils.logger import trading_logger
        print("✅ Logger module imported successfully")
        
        from src.utils.technical_indicators import TechnicalIndicators
        print("✅ Technical indicators module imported successfully")
        
        from src.utils.email_sender import EmailSender
        print("✅ Email sender module imported successfully")
        
        from src.core.data_manager import DataManager
        print("✅ Data manager module imported successfully")
        
        from src.agents.analysis_agent import AnalysisAgent
        print("✅ Analysis agent module imported successfully")
        
        from src.agents.news_agent import NewsAgent
        print("✅ News agent module imported successfully")
        
        from src.agents.master_agent import MasterAgent
        print("✅ Master agent module imported successfully")
        
        print("✅ All core modules imported successfully!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_config_files():
    """Test if configuration files exist"""
    print("\n🔍 Testing configuration files...")
    
    config_files = [
        "config/config.yaml",
        "rules.json"
    ]
    
    all_exist = True
    for config_file in config_files:
        if Path(config_file).exists():
            print(f"✅ {config_file} exists")
        else:
            print(f"❌ {config_file} missing")
            all_exist = False
    
    return all_exist

def test_directory_structure():
    """Test if directory structure is correct"""
    print("\n🔍 Testing directory structure...")
    
    required_dirs = [
        "src",
        "src/agents",
        "src/core", 
        "src/utils",
        "config",
        "logs"
    ]
    
    all_exist = True
    for directory in required_dirs:
        if Path(directory).exists():
            print(f"✅ {directory}/ directory exists")
        else:
            print(f"❌ {directory}/ directory missing")
            all_exist = False
    
    return all_exist

def test_basic_functionality():
    """Test basic functionality without external APIs"""
    print("\n🔍 Testing basic functionality...")
    
    try:
        # Test logger
        from src.utils.logger import trading_logger
        logger = trading_logger.get_logger("test")
        logger.info("Test log message")
        print("✅ Logger functionality working")
        
        # Test technical indicators
        from src.utils.technical_indicators import TechnicalIndicators
        ti = TechnicalIndicators()
        print("✅ Technical indicators initialized")
        
        # Test data manager (without external APIs)
        from src.core.data_manager import DataManager
        try:
            dm = DataManager()
            print("✅ Data manager initialized")
        except Exception as e:
            print(f"⚠️  Data manager initialization warning: {e}")
        
        print("✅ Basic functionality tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
        return False

def test_dependencies():
    """Test if required Python packages are available"""
    print("\n🔍 Testing Python dependencies...")
    
    required_packages = [
        'pandas',
        'numpy', 
        'yfinance',
        'requests',
        'yaml',
        'structlog',
        'schedule'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} available")
        except ImportError:
            print(f"❌ {package} missing")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
        print("Install missing packages with: pip install -r requirements.txt")
        return False
    else:
        print("✅ All required packages available!")
        return True

def main():
    """Main test function"""
    print("🚀 AI Trading Bot - Installation Test")
    print("=" * 50)
    
    # Run all tests
    tests = [
        ("Module Imports", test_imports),
        ("Configuration Files", test_config_files),
        ("Directory Structure", test_directory_structure),
        ("Python Dependencies", test_dependencies),
        ("Basic Functionality", test_basic_functionality)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! AI Trading Bot is ready to use.")
        print("\nNext steps:")
        print("1. Configure your API keys in .env file")
        print("2. Review config/config.yaml settings")
        print("3. Run: python src/main.py")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please fix issues before proceeding.")
        print("\nCommon solutions:")
        print("- Install missing packages: pip install -r requirements.txt")
        print("- Check file permissions and directory structure")
        print("- Verify Python version (3.8+ required)")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
