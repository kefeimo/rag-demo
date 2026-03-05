"""Test code doc generator with specific file."""

import sys
from pathlib import Path
from code_doc_generator import CodeDocGenerator
import json

def test_with_specific_file():
    """Test with a specific props file."""
    
    repo_path = Path('/tmp/visa-chart-components')
    if not repo_path.exists():
        print("❌ Repository not found at /tmp/visa-chart-components")
        print("   Please clone it first:")
        print("   cd /tmp && git clone --depth=1 https://github.com/visa/visa-chart-components.git")
        return
    
    generator = CodeDocGenerator(
        repo_path=str(repo_path),
        repo_name='visa/visa-chart-components'
    )
    
    # Test with specific file
    test_file = repo_path / 'packages/data-table/src/components/data-table/data-table-props.ts'
    
    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        return
    
    print(f"\n📂 Testing with: {test_file.relative_to(repo_path)}")
    print("=" * 60)
    
    content = test_file.read_text(encoding='utf-8')
    
    print(f"\n📄 File size: {len(content)} bytes")
    print(f"📄 Lines: {len(content.splitlines())}")
    
    # Test extraction methods
    print("\n🔍 Extracting interfaces...")
    interfaces = generator.extract_interfaces(content, test_file)
    print(f"   Found {len(interfaces)} interfaces")
    
    print("\n🔍 Extracting component props...")
    component_props = generator.extract_component_props(content, test_file)
    print(f"   Found {len(component_props)} component props interfaces")
    
    print("\n🔍 Extracting types...")
    types = generator.extract_types(content, test_file)
    print(f"   Found {len(types)} type aliases")
    
    print("\n🔍 Extracting functions...")
    functions = generator.extract_functions(content, test_file)
    print(f"   Found {len(functions)} functions")
    
    # Show details
    all_items = interfaces + component_props + types + functions
    
    if all_items:
        print("\n" + "=" * 60)
        print("EXTRACTED ITEMS DETAILS")
        print("=" * 60)
        
        for i, item in enumerate(all_items[:3], 1):  # Show first 3
            print(f"\n{i}. {item['name']} ({item['type']})")
            print(f"   File: {item['file_path']}")
            print(f"   Description: {item.get('description', 'N/A')[:100]}...")
            
            if item['type'] in ['interface', 'component_props']:
                print(f"   Properties: {len(item.get('props', []))}")
                # Show first 3 props
                for prop in item.get('props', [])[:3]:
                    print(f"      - {prop['name']}: {prop['type']}")
                    if prop.get('description'):
                        print(f"        {prop['description'][:80]}...")
        
        # Generate API doc for first item
        if all_items:
            print("\n" + "=" * 60)
            print("SAMPLE API DOCUMENTATION")
            print("=" * 60)
            
            api_doc = generator.generate_api_doc(all_items[0])
            print("\n📄 Content preview (first 500 chars):")
            print(api_doc['content'][:500])
            print("\n...")
            
            print("\n📊 Metadata:")
            for key, value in api_doc['metadata'].items():
                print(f"   {key}: {value}")
    else:
        print("\n❌ No items extracted!")
        print("\n🔍 Debugging: Checking for 'export interface' patterns...")
        export_interfaces = content.count('export interface')
        print(f"   Found 'export interface' {export_interfaces} times in file")
        
        # Show first export interface
        import re
        matches = list(re.finditer(r'export interface \w+', content))
        if matches:
            print(f"\n   First few matches:")
            for match in matches[:3]:
                start = max(0, match.start() - 50)
                end = min(len(content), match.end() + 100)
                snippet = content[start:end].replace('\n', ' ')
                print(f"   ...{snippet}...")

if __name__ == '__main__':
    test_with_specific_file()
