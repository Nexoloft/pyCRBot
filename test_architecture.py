#!/usr/bin/env python3
"""
Test script to verify the refactored architecture
"""

def test_imports():
    """Test that all modules can be imported without errors"""
    print("🧪 Testing imports...")
    
    try:
        from main import main
        print("✅ main.py imported successfully")
        
        from emulator_bot import EmulatorBot
        print("✅ EmulatorBot imported successfully")
        
        from battle_runner import BattleRunner
        print("✅ BattleRunner imported successfully")
        
        from battle_strategy import BattleStrategy
        print("✅ BattleStrategy imported successfully")
        
        from logger import Logger
        print("✅ Logger imported successfully")
        
        from emulators.base import BaseEmulatorController
        print("✅ BaseEmulatorController imported successfully")
        
        from emulators.memu import MemuController
        print("✅ MemuController imported successfully")
        
        from gui import ClashRoyaleBotGUI
        print("✅ GUI imported successfully")
        
        print("\n🎉 All imports successful! Refactoring completed.")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False


def test_architecture():
    """Test basic architecture functionality"""
    print("\n🏗️  Testing architecture...")
    
    try:
        # Test strategy initialization
        from battle_strategy import BattleStrategy
        strategy = BattleStrategy()
        print("✅ BattleStrategy can be instantiated")
        
        # Test logger
        from logger import Logger
        logger = Logger("test")
        print("✅ Logger can be instantiated")
        
        # Test emulator controller
        from emulators.memu import MemuController
        controller = MemuController("21503", "test_instance")
        print("✅ MemuController can be instantiated")
        
        print("\n🎯 Architecture test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Architecture test failed: {e}")
        return False


def main():
    """Run all tests"""
    print("🚀 Clash Royale Bot - PyClashBot Style Architecture Test")
    print("=" * 60)
    
    imports_ok = test_imports()
    architecture_ok = test_architecture()
    
    if imports_ok and architecture_ok:
        print("\n🏆 All tests passed! Your refactored codebase is ready.")
        print("\n📖 Usage:")
        print("  python run.py --gui          # Launch GUI")
        print("  python run.py --headless     # Single emulator")
        print("  python run.py --multi 3      # 3 emulators")
        print("  python run.py --help         # Show help")
    else:
        print("\n❌ Some tests failed. Please check the errors above.")


if __name__ == "__main__":
    main()
