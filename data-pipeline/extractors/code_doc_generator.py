"""
Code Documentation Generator - Extract API docs from source code.

This module extracts structured API documentation from TypeScript/JavaScript source files:
- TypeScript interfaces and types
- JSDoc comments
- Component props (React/Angular/Vue)
- Function signatures

Part of RAG Data Pipeline Framework (Pillar 2).
"""

import logging
import re
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import hashlib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CodeDocGenerator:
    """
    Extract API documentation from TypeScript/JavaScript source code.
    
    Supports:
    - TypeScript interfaces and types
    - JSDoc comments
    - Component props
    - Exported functions and classes
    """
    
    def __init__(self, repo_path: str, repo_name: str):
        """
        Initialize code documentation generator.
        
        Args:
            repo_path: Path to cloned repository
            repo_name: Repository name (org/repo format)
        """
        self.repo_path = Path(repo_path)
        self.repo_name = repo_name
        self.excluded_dirs = {
            'node_modules', 'dist', 'build', '.next', '__pycache__',
            'coverage', '.pytest_cache', 'htmlcov', '.tox', 'venv', 
            '.git', '.github', 'tests', '__tests__', 'test', 'spec'
        }
        
    def find_source_files(self) -> List[Path]:
        """
        Find all TypeScript/JavaScript source files.
        
        Returns:
            List of source file paths
        """
        source_files = []
        extensions = {'.ts', '.tsx', '.js', '.jsx'}
        
        for file_path in self.repo_path.rglob('*'):
            # Skip excluded directories
            if any(excluded in file_path.parts for excluded in self.excluded_dirs):
                continue
                
            if file_path.suffix in extensions and file_path.is_file():
                source_files.append(file_path)
        
        logger.info(f"Found {len(source_files)} source files")
        return source_files
    
    def extract_interfaces(self, content: str, file_path: Path) -> List[Dict]:
        """
        Extract TypeScript interfaces with JSDoc comments.
        
        Args:
            content: File content
            file_path: Path to source file
            
        Returns:
            List of interface documentation dictionaries
        """
        interfaces = []
        
        # Pattern: export interface with optional JSDoc (braces may be on next line)
        # First try to match interfaces with their bodies
        pattern = r'(?:(/\*\*[\s\S]*?\*/)\s*)?export\s+interface\s+(\w+)\s*\{([\s\S]*?)(?=\nexport|\ninterface|$)'
        
        for match in re.finditer(pattern, content):
            jsdoc, interface_name, interface_body = match.groups()
            
            # Only process if we have a meaningful body (has at least one property)
            if not interface_body or ':' not in interface_body:
                continue
            
            # Parse JSDoc if present
            description = self._parse_jsdoc_description(jsdoc) if jsdoc else f"{interface_name} interface"
            props = self._parse_interface_props_with_jsdoc(interface_body)
            
            interfaces.append({
                'type': 'interface',
                'name': interface_name,
                'description': description,
                'props': props,
                'file_path': str(file_path.relative_to(self.repo_path))
            })
        
        return interfaces
    
    def extract_types(self, content: str, file_path: Path) -> List[Dict]:
        """
        Extract TypeScript type aliases with JSDoc comments.
        
        Args:
            content: File content
            file_path: Path to source file
            
        Returns:
            List of type documentation dictionaries
        """
        types = []
        
        # Pattern: JSDoc comment followed by type
        pattern = r'(/\*\*[\s\S]*?\*/)\s*export\s+type\s+(\w+)\s*=([^;]+);'
        
        for match in re.finditer(pattern, content):
            jsdoc, type_name, type_def = match.groups()
            
            description = self._parse_jsdoc_description(jsdoc)
            
            types.append({
                'type': 'type',
                'name': type_name,
                'description': description,
                'definition': type_def.strip(),
                'file_path': str(file_path.relative_to(self.repo_path))
            })
        
        return types
    
    def extract_functions(self, content: str, file_path: Path) -> List[Dict]:
        """
        Extract exported functions with JSDoc comments.
        
        Args:
            content: File content
            file_path: Path to source file
            
        Returns:
            List of function documentation dictionaries
        """
        functions = []
        
        # Pattern: JSDoc comment followed by export function
        pattern = r'(/\*\*[\s\S]*?\*/)\s*export\s+(?:function|const)\s+(\w+)\s*[=:]?\s*(?:\(|<)'
        
        for match in re.finditer(pattern, content):
            jsdoc, func_name = match.groups()
            
            description = self._parse_jsdoc_description(jsdoc)
            params = self._parse_jsdoc_params(jsdoc)
            returns = self._parse_jsdoc_returns(jsdoc)
            
            functions.append({
                'type': 'function',
                'name': func_name,
                'description': description,
                'params': params,
                'returns': returns,
                'file_path': str(file_path.relative_to(self.repo_path))
            })
        
        return functions
    
    def extract_component_props(self, content: str, file_path: Path) -> List[Dict]:
        """
        Extract React/Vue component props interfaces.
        
        Args:
            content: File content
            file_path: Path to source file
            
        Returns:
            List of component props documentation
        """
        props_interfaces = []
        
        # Look for Props interfaces (common naming: ComponentNameProps, IComponentProps)
        pattern = r'(?:(/\*\*[\s\S]*?\*/)\s*)?export\s+interface\s+(I?\w+Props)\s*\{([\s\S]*?)(?=\nexport|\ninterface|$)'
        
        for match in re.finditer(pattern, content):
            jsdoc, props_name, props_body = match.groups()
            
            # Only process if we have a meaningful body
            if not props_body or ':' not in props_body:
                continue
            
            description = self._parse_jsdoc_description(jsdoc) if jsdoc else f"{props_name} interface"
            props = self._parse_interface_props_with_jsdoc(props_body)
            
            # Extract component name (remove "Props" suffix and optional "I" prefix)
            component_name = props_name.replace('Props', '').lstrip('I')
            
            props_interfaces.append({
                'type': 'component_props',
                'component': component_name,
                'name': props_name,
                'description': description,
                'props': props,
                'file_path': str(file_path.relative_to(self.repo_path))
            })
        
        return props_interfaces
    
    def _parse_jsdoc_description(self, jsdoc: str) -> str:
        """Extract description from JSDoc comment."""
        # Remove /** and */ markers
        clean = jsdoc.replace('/**', '').replace('*/', '').strip()
        
        # Remove leading * from each line
        lines = [line.lstrip(' *') for line in clean.split('\n')]
        
        # Extract description (text before first @tag)
        description_lines = []
        for line in lines:
            if line.startswith('@'):
                break
            description_lines.append(line)
        
        return '\n'.join(description_lines).strip()
    
    def _parse_jsdoc_params(self, jsdoc: str) -> List[Dict]:
        """Extract @param tags from JSDoc."""
        params = []
        param_pattern = r'@param\s+(?:{([^}]+)}\s+)?(\w+)\s+-?\s*(.*)'
        
        for match in re.finditer(param_pattern, jsdoc):
            param_type, param_name, param_desc = match.groups()
            params.append({
                'name': param_name,
                'type': param_type or 'any',
                'description': param_desc.strip()
            })
        
        return params
    
    def _parse_jsdoc_returns(self, jsdoc: str) -> Optional[Dict]:
        """Extract @returns tag from JSDoc."""
        returns_pattern = r'@returns?\s+(?:{([^}]+)}\s+)?(.*)'
        match = re.search(returns_pattern, jsdoc)
        
        if match:
            return_type, return_desc = match.groups()
            return {
                'type': return_type or 'any',
                'description': return_desc.strip()
            }
        
        return None
    
    def _parse_interface_props(self, interface_body: str) -> List[Dict]:
        """Parse interface properties."""
        props = []
        
        # Pattern: property: type; with optional JSDoc
        # Handle multi-line properties
        prop_pattern = r'(\w+)(\??):\s*([^;]+);'
        
        for match in re.finditer(prop_pattern, interface_body):
            prop_name, optional, prop_type = match.groups()
            props.append({
                'name': prop_name,
                'type': prop_type.strip(),
                'optional': bool(optional),
                'description': ''  # Could enhance by looking for inline comments
            })
        
        return props
    
    def _parse_interface_props_with_jsdoc(self, interface_body: str) -> List[Dict]:
        """
        Parse interface properties with their JSDoc comments.
        Handles properties that have JSDoc comments above them.
        """
        props = []
        
        # Split by properties - look for JSDoc comment followed by property
        # Pattern: optional JSDoc comment followed by property: type;
        sections = re.split(r'(/\*\*[\s\S]*?\*/)', interface_body)
        
        current_jsdoc = None
        for section in sections:
            section = section.strip()
            if not section:
                continue
                
            # Check if this is a JSDoc comment
            if section.startswith('/**'):
                current_jsdoc = section
            else:
                # Look for property definitions
                prop_matches = re.finditer(r'(\w+)(\??):\s*([^;]+);', section)
                for match in prop_matches:
                    prop_name, optional, prop_type = match.groups()
                    
                    # Extract description from JSDoc if available
                    description = ''
                    if current_jsdoc:
                        # Look for @shortDescription or main description
                        short_desc_match = re.search(r'@shortDescription\s+(.+?)(?=\n\s*\*\s*@|\n\s*\*/)', current_jsdoc, re.DOTALL)
                        if short_desc_match:
                            description = short_desc_match.group(1).strip()
                        else:
                            description = self._parse_jsdoc_description(current_jsdoc)
                    
                    props.append({
                        'name': prop_name,
                        'type': prop_type.strip(),
                        'optional': bool(optional),
                        'description': description
                    })
                    
                    # Reset JSDoc for next property
                    current_jsdoc = None
        
        return props
    
    def generate_api_doc(self, code_item: Dict) -> Dict:
        """
        Convert code item to API documentation format.
        
        Args:
            code_item: Extracted code item (interface/type/function/component)
            
        Returns:
            API documentation dictionary with content and metadata
        """
        # Generate readable API documentation
        content = self._format_api_content(code_item)
        
        # Generate metadata
        metadata = {
            'source': 'code_docs',
            'repo_name': self.repo_name,
            'file_path': code_item['file_path'],
            'api_type': code_item['type'],
            'api_name': code_item['name'],
            'doc_id': self._generate_doc_id(content),
            'doc_type': 'api',
            'audience': 'external',
            'extracted_at': datetime.utcnow().isoformat(),
            'auto_generated': True,
            'generation_method': 'code_doc_generator',
            'source_language': 'typescript'  # Could be detected from file extension
        }
        
        # Add package if in packages/ directory
        if 'packages/' in code_item['file_path']:
            package = code_item['file_path'].split('packages/')[1].split('/')[0]
            metadata['package'] = package
        
        # Add component name for component props
        if code_item['type'] == 'component_props':
            metadata['component'] = code_item['component']
        
        return {
            'content': content,
            'metadata': metadata
        }
    
    def _format_api_content(self, code_item: Dict) -> str:
        """Format code item as readable API documentation."""
        lines = []
        
        # Header
        lines.append(f"# {code_item['name']}")
        lines.append('')
        
        # Description
        if code_item.get('description'):
            lines.append(code_item['description'])
            lines.append('')
        
        # Type-specific formatting
        if code_item['type'] == 'interface':
            lines.append('## Properties')
            lines.append('')
            for prop in code_item.get('props', []):
                optional = '?' if prop.get('optional') else ''
                lines.append(f"- `{prop['name']}{optional}: {prop['type']}`")
                if prop.get('description'):
                    lines.append(f"  - {prop['description']}")
            
        elif code_item['type'] == 'type':
            lines.append('## Type Definition')
            lines.append('')
            lines.append(f"```typescript\n{code_item['definition']}\n```")
            
        elif code_item['type'] == 'function':
            lines.append('## Parameters')
            lines.append('')
            for param in code_item.get('params', []):
                lines.append(f"- `{param['name']}: {param['type']}`")
                if param.get('description'):
                    lines.append(f"  - {param['description']}")
            
            if code_item.get('returns'):
                lines.append('')
                lines.append('## Returns')
                lines.append('')
                returns = code_item['returns']
                lines.append(f"`{returns['type']}` - {returns.get('description', '')}")
        
        elif code_item['type'] == 'component_props':
            lines.append(f"## {code_item['component']} Props")
            lines.append('')
            for prop in code_item.get('props', []):
                optional = ' (optional)' if prop.get('optional') else ''
                lines.append(f"- **{prop['name']}**{optional}: `{prop['type']}`")
                if prop.get('description'):
                    lines.append(f"  - {prop['description']}")
        
        # File reference
        lines.append('')
        lines.append(f"*Source: `{code_item['file_path']}`*")
        
        return '\n'.join(lines)
    
    def _generate_doc_id(self, content: str) -> str:
        """Generate unique document ID using SHA256 hash."""
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def extract_all(self, max_files: Optional[int] = None) -> List[Dict]:
        """
        Extract API documentation from all source files.
        
        Args:
            max_files: Maximum number of files to process (for testing)
            
        Returns:
            List of API documentation dictionaries
        """
        source_files = self.find_source_files()
        
        if max_files:
            source_files = source_files[:max_files]
            logger.info(f"Processing first {max_files} files for testing")
        
        all_docs = []
        
        for file_path in source_files:
            try:
                content = file_path.read_text(encoding='utf-8')
            except UnicodeDecodeError:
                try:
                    content = file_path.read_text(encoding='latin-1')
                except Exception as e:
                    logger.warning(f"Failed to read {file_path}: {e}")
                    continue
            
            # Extract all code items
            interfaces = self.extract_interfaces(content, file_path)
            types = self.extract_types(content, file_path)
            functions = self.extract_functions(content, file_path)
            component_props = self.extract_component_props(content, file_path)
            
            # Convert to API docs
            for item in interfaces + types + functions + component_props:
                api_doc = self.generate_api_doc(item)
                all_docs.append(api_doc)
        
        logger.info(f"Extracted {len(all_docs)} API documentation entries")
        return all_docs


if __name__ == '__main__':
    # Example usage
    generator = CodeDocGenerator(
        repo_path='/tmp/visa-chart-components',
        repo_name='visa/visa-chart-components'
    )
    
    # Extract from first 10 files for testing
    docs = generator.extract_all(max_files=10)
    
    print(f"\n✅ Extracted {len(docs)} API documentation entries")
    
    # Show sample
    if docs:
        print(f"\n📄 Sample API Doc:")
        print(f"   Name: {docs[0]['metadata']['api_name']}")
        print(f"   Type: {docs[0]['metadata']['api_type']}")
        print(f"   File: {docs[0]['metadata']['file_path']}")
        print(f"   Content preview: {docs[0]['content'][:200]}...")
