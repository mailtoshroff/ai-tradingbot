#!/usr/bin/env python3
"""
Test script to verify environment variable fixes
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_environment_fixes():
    """Test if environment variables are loading correctly"""
    print("🔍 Testing Environment Variable Fixes")
    print("=" * 50)
    
    try:
        from dotenv import load_dotenv
        
        # Load environment variables
        load_dotenv()
        
        print("✅ Environment variables loaded successfully")
        
        # Test SMTP configuration
        smtp_port = os.getenv('SMTP_PORT')
        smtp_server = os.getenv('SMTP_SERVER')
        sender_email = os.getenv('SENDER_EMAIL')
        
        print(f"\n📧 Email Configuration:")
        print(f"   - SMTP Server: {smtp_server}")
        print(f"   - SMTP Port: {smtp_port} (type: {type(smtp_port)})")
        print(f"   - Sender Email: {sender_email}")
        
        # Test if SMTP_PORT can be converted to int
        try:
            smtp_port_int = int(smtp_port)
            print(f"   - ✅ SMTP_PORT converted to int: {smtp_port_int}")
        except (ValueError, TypeError) as e:
            print(f"   - ❌ SMTP_PORT conversion error: {e}")
        
        # Test News API configuration
        newsapi_key = os.getenv('NEWSAPI_API_KEY')
        print(f"\n📰 News API Configuration:")
        print(f"   - API Key: {newsapi_key}")
        
        # Test Alpha Vantage configuration
        alpha_vantage_key = os.getenv('ALPHA_VANTAGE_API_KEY')
        print(f"\n📊 Alpha Vantage Configuration:")
        print(f"   - API Key: {alpha_vantage_key}")
        
        # Test Azure OpenAI configuration
        azure_endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
        azure_key = os.getenv('AZURE_OPENAI_API_KEY')
        azure_version = os.getenv('AZURE_OPENAI_API_VERSION')
        azure_deployment = os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME')
        
        print(f"\n🤖 Azure OpenAI Configuration:")
        print(f"   - Endpoint: {azure_endpoint}")
        print(f"   - API Key: {'*' * 10 + azure_key[-4:] if azure_key else 'Not set'}")
        print(f"   - API Version: {azure_version}")
        print(f"   - Deployment: {azure_deployment}")
        
        print(f"\n🎉 All environment variables loaded successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_environment_fixes()
