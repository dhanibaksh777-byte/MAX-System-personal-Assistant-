"""Quick validation test for Max Assistant modules."""
import sys
sys.path.insert(0, '.')

try:
    from config import GROQ_API_KEY, MODEL_NAME, ASSISTANT_NAME
    print(f"[OK] Config loaded - Assistant: {ASSISTANT_NAME}, Model: {MODEL_NAME}")
    
    from memory_manager import MemoryManager
    mem = MemoryManager()
    print(f"[OK] Memory Manager initialized")
    
    from system_controller import SystemController
    sys_ctrl = SystemController()
    print(f"[OK] System Controller initialized - {len(sys_ctrl.APP_COMMANDS)} apps mapped")
    
    from assistant_core import AssistantCore
    core = AssistantCore()
    print(f"[OK] Assistant Core initialized - {len(core.tools)} tools available")
    
    from server import app
    print(f"[OK] Flask server ready")
    
    api_ready = bool(GROQ_API_KEY and GROQ_API_KEY != "your_groq_api_key_here")
    print(f"\n{'[OK]' if api_ready else '[!!]'} API Key configured: {api_ready}")
    if not api_ready:
        print("     Add your Groq API key to .env file!")
        print("     Get FREE key at: https://console.groq.com")
    
    print("\n=== All modules validated successfully! ===")
    
except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()
