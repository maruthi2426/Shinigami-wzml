#!/usr/bin/env python3
"""
Test script to verify WebScrapper CloudScraper fix works correctly
Run this to verify the migration from Selenium to CloudScraper is complete
"""

import sys
import os
import importlib.util
from pathlib import Path

def test_imports():
    """Test that all required modules can be imported"""
    print("\n" + "="*60)
    print("TESTING IMPORTS")
    print("="*60)
    
    required_modules = {
        'cloudscraper': 'CloudScraper library',
        'requests': 'HTTP library',
        'beautifulsoup4': 'HTML parser',
        're': 'Regex module',
        'time': 'Time module'
    }
    
    failed = []
    for module, description in required_modules.items():
        try:
            __import__(module)
            print(f"✅ {module:20} - {description}")
        except ImportError as e:
            print(f"❌ {module:20} - {description} - ERROR: {e}")
            failed.append((module, description))
    
    if failed:
        print(f"\n❌ Missing {len(failed)} required module(s)!")
        print("\nInstall with:")
        for module, _ in failed:
            print(f"  pip install {module}")
        return False
    
    print("\n✅ All imports successful!")
    return True

def test_webscrapper_no_selenium():
    """Verify webscrapper.py no longer imports Selenium"""
    print("\n" + "="*60)
    print("TESTING WEBSCRAPPER DEPENDENCIES")
    print("="*60)
    
    webscrapper_paths = [
        "bot/webscrapper.py",
        "webscrapper.py"
    ]
    
    for webscrapper_path in webscrapper_paths:
        if not os.path.exists(webscrapper_path):
            print(f"⚠️  {webscrapper_path} not found, skipping...")
            continue
        
        print(f"\nChecking {webscrapper_path}...")
        with open(webscrapper_path, 'r') as f:
            content = f.read()
        
        # Check for Selenium imports
        has_selenium = 'from selenium' in content or 'import selenium' in content
        has_webdriver_manager = 'webdriver_manager' in content
        has_cloudscraper = 'cloudscraper' in content
        
        print(f"  Selenium imports: {'❌ FOUND (BAD)' if has_selenium else '✅ NOT FOUND (GOOD)'}")
        print(f"  WebDriver Manager: {'❌ FOUND (BAD)' if has_webdriver_manager else '✅ NOT FOUND (GOOD)'}")
        print(f"  CloudScraper: {'✅ FOUND (GOOD)' if has_cloudscraper else '❌ NOT FOUND (BAD)'}")
        
        if has_selenium or has_webdriver_manager:
            print(f"\n❌ {webscrapper_path} still has Selenium imports!")
            return False
        
        if not has_cloudscraper:
            print(f"\n⚠️  {webscrapper_path} doesn't have CloudScraper, might use old code")
    
    print("\n✅ WebScrapper dependencies are correct!")
    return True

def test_scraper_class():
    """Test that VegamoviesScraper can be instantiated"""
    print("\n" + "="*60)
    print("TESTING SCRAPER INSTANTIATION")
    print("="*60)
    
    bot_dir = Path(__file__).parent / "bot"
    webscrapper_path = bot_dir / "webscrapper.py"
    
    if not webscrapper_path.exists():
        print(f"⚠️  {webscrapper_path} not found, skipping class test...")
        return True
    
    try:
        spec = importlib.util.spec_from_file_location("webscrapper_module", str(webscrapper_path))
        if spec is None or spec.loader is None:
            print(f"❌ Failed to create module spec")
            return False
        
        webscrapper_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(webscrapper_module)
        
        print(f"✅ WebScrapper module loaded successfully")
        
        # Try to instantiate the scraper
        if not hasattr(webscrapper_module, 'VegamoviesScraper'):
            print(f"❌ VegamoviesScraper class not found")
            return False
        
        scraper = webscrapper_module.VegamoviesScraper()
        print(f"✅ VegamoviesScraper instance created successfully")
        
        # Check for required methods
        required_methods = ['scrape', 'get_links', '_resolve_shortener', '_fetch_page']
        for method in required_methods:
            if not hasattr(scraper, method):
                print(f"❌ Method {method} not found in VegamoviesScraper")
                return False
            print(f"  ✅ Method {method} exists")
        
        print(f"\n✅ Scraper class structure is correct!")
        return True
        
    except SyntaxError as e:
        print(f"❌ Syntax error: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_scrape_website_function():
    """Test that scrape_website function exists and is callable"""
    print("\n" + "="*60)
    print("TESTING SCRAPE_WEBSITE FUNCTION")
    print("="*60)
    
    bot_dir = Path(__file__).parent / "bot"
    webscrapper_path = bot_dir / "webscrapper.py"
    
    if not webscrapper_path.exists():
        print(f"⚠️  {webscrapper_path} not found, skipping function test...")
        return True
    
    try:
        spec = importlib.util.spec_from_file_location("webscrapper_module", str(webscrapper_path))
        if spec is None or spec.loader is None:
            return False
        
        webscrapper_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(webscrapper_module)
        
        if not hasattr(webscrapper_module, 'scrape_website'):
            print(f"❌ scrape_website function not found")
            return False
        
        print(f"✅ scrape_website function exists")
        print(f"✅ Function is callable: {callable(webscrapper_module.scrape_website)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Run all tests"""
    print("\n")
    print("╔" + "="*58 + "╗")
    print("║" + " "*58 + "║")
    print("║" + "  WEBSCRAPPER CLOUDSCRAPER MIGRATION TEST".center(58) + "║")
    print("║" + " "*58 + "║")
    print("╚" + "="*58 + "╝")
    
    tests = [
        ("Import Check", test_imports),
        ("Selenium Removal Check", test_webscrapper_no_selenium),
        ("Scraper Class Test", test_scraper_class),
        ("scrape_website Function Test", test_scrape_website_function),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ Test '{test_name}' crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:10} - {test_name}")
    
    print("="*60)
    print(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! WebScrapper migration is complete!")
        return 0
    else:
        print(f"\n❌ {total - passed} test(s) failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
