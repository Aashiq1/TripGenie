import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_openai_key():
    """Test if OpenAI API key is properly configured"""
    print("🔍 Testing OpenAI API Key...")
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("❌ OPENAI_API_KEY not found in .env file")
        return False
    
    if api_key == "your_openai_key_here":
        print("❌ OPENAI_API_KEY still has placeholder value")
        print("   Please replace 'your_openai_key_here' with your actual API key")
        return False
    
    if not api_key.startswith("sk-"):
        print("❌ OPENAI_API_KEY doesn't look like a valid OpenAI key")
        print("   OpenAI keys should start with 'sk-'")
        return False
    
    print("✅ OPENAI_API_KEY looks valid!")
    print(f"   Key starts with: {api_key[:7]}...")
    
    # Test actual API call
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        
        # Simple test call
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hello! This is a test."}],
            max_tokens=10
        )
        
        print("✅ OpenAI API call successful!")
        return True
        
    except ImportError:
        print("⚠️  OpenAI library not installed yet")
        print("   Run: pip install openai")
        return False
        
    except Exception as e:
        print(f"❌ OpenAI API call failed: {e}")
        return False

def test_anthropic_key():
    """Test if Anthropic API key is properly configured"""
    print("\n🔍 Testing Anthropic API Key...")
    api_key = os.getenv("ANTHROPIC_API_KEY")
    
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not found in .env file")
        return False
    
    if api_key == "your_anthropic_key_here":
        print("❌ ANTHROPIC_API_KEY still has placeholder value")
        print("   Please replace 'your_anthropic_key_here' with your actual API key")
        return False
    
    if not api_key.startswith("sk-ant-"):
        print("❌ ANTHROPIC_API_KEY doesn't look like a valid Anthropic key")
        print("   Anthropic keys should start with 'sk-ant-'")
        return False
    
    print("✅ ANTHROPIC_API_KEY looks valid!")
    print(f"   Key starts with: {api_key[:10]}...")
    
    # Test actual API call
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        
        # Simple test call
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=10,
            messages=[{"role": "user", "content": "Hello! This is a test."}]
        )
        
        print("✅ Anthropic API call successful!")
        return True
        
    except ImportError:
        print("⚠️  Anthropic library not installed yet")
        print("   Run: pip install anthropic")
        return False
        
    except Exception as e:
        print(f"❌ Anthropic API call failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing AI API Key Configuration...")
    print("=" * 50)
    
    openai_success = test_openai_key()
    anthropic_success = test_anthropic_key()
    
    print("\n" + "=" * 50)
    print("📊 SUMMARY:")
    print(f"   OpenAI:    {'✅ Working' if openai_success else '❌ Not working'}")
    print(f"   Anthropic: {'✅ Working' if anthropic_success else '❌ Not working'}")
    
    if openai_success or anthropic_success:
        print("\n🎉 At least one AI API is working! You can start building!")
    else:
        print("\n⚠️  No AI APIs are working. Please check your .env file.") 