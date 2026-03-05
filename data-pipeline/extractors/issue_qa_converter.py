"""
Issue-to-Q&A Converter - Convert GitHub Issues to Q&A pairs.

This module extracts Q&A pairs from GitHub Issues and Pull Requests:
- Closed issues with comments
- Issue title + body = Question
- Top comments/resolution = Answer
- Audience metadata (internal/external)
- Issue classification (bug/feature/merge/release)

Part of RAG Data Pipeline Framework (Pillar 3).
"""

import logging
import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import hashlib
import subprocess
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IssueQAConverter:
    """
    Convert GitHub Issues to Q&A pairs for RAG ingestion.
    
    Supports:
    - Closed issues with discussions
    - Audience classification (internal vs external)
    - Issue type classification (bug/feature/merge/release)
    - Context tagging (development/ci_cd/production)
    """
    
    def __init__(self, repo_name: str, github_token: Optional[str] = None):
        """
        Initialize issue-to-Q&A converter.
        
        Args:
            repo_name: Repository name (org/repo format)
            github_token: Optional GitHub API token for higher rate limits
        """
        self.repo_name = repo_name
        self.github_token = github_token
        self.api_base = f"https://api.github.com/repos/{repo_name}"
        
    def fetch_closed_issues(self, max_issues: int = 100) -> List[Dict]:
        """
        Fetch closed issues from GitHub API.
        
        Args:
            max_issues: Maximum number of issues to fetch
            
        Returns:
            List of issue dictionaries
        """
        issues = []
        page = 1
        per_page = min(100, max_issues)
        
        while len(issues) < max_issues:
            # Build curl command
            url = f"{self.api_base}/issues?state=closed&per_page={per_page}&page={page}"
            cmd = ['curl', '-s']
            
            if self.github_token:
                cmd.extend(['-H', f'Authorization: token {self.github_token}'])
            
            cmd.append(url)
            
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode != 0:
                    logger.error(f"Failed to fetch issues: {result.stderr}")
                    break
                
                page_issues = json.loads(result.stdout)
                
                if not page_issues or not isinstance(page_issues, list):
                    break
                
                # Filter out pull requests (they appear in issues endpoint)
                actual_issues = [
                    issue for issue in page_issues 
                    if 'pull_request' not in issue
                ]
                
                issues.extend(actual_issues)
                
                if len(page_issues) < per_page:
                    break  # No more issues
                
                page += 1
                time.sleep(0.5)  # Rate limiting courtesy
                
            except subprocess.TimeoutExpired:
                logger.error("Timeout fetching issues")
                break
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                break
            except Exception as e:
                logger.error(f"Error fetching issues: {e}")
                break
        
        logger.info(f"Fetched {len(issues)} closed issues")
        return issues[:max_issues]
    
    def fetch_issue_comments(self, issue_number: int) -> List[Dict]:
        """
        Fetch comments for a specific issue.
        
        Args:
            issue_number: Issue number
            
        Returns:
            List of comment dictionaries
        """
        url = f"{self.api_base}/issues/{issue_number}/comments"
        cmd = ['curl', '-s']
        
        if self.github_token:
            cmd.extend(['-H', f'Authorization: token {self.github_token}'])
        
        cmd.append(url)
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                logger.error(f"Failed to fetch comments for issue #{issue_number}")
                return []
            
            comments = json.loads(result.stdout)
            
            if not isinstance(comments, list):
                return []
            
            return comments
            
        except Exception as e:
            logger.error(f"Error fetching comments for issue #{issue_number}: {e}")
            return []
    
    def classify_issue_type(self, issue: Dict) -> str:
        """
        Classify issue type based on title and labels.
        
        Args:
            issue: Issue dictionary
            
        Returns:
            Issue type: 'merge', 'release', 'bug', 'feature', 'question', 'documentation', 'other'
        """
        title_lower = issue.get('title', '').lower()
        labels = [label['name'].lower() for label in issue.get('labels', [])]
        
        # Check title patterns
        if any(keyword in title_lower for keyword in ['merge', 'back to', 'into']):
            return 'merge'
        
        if any(keyword in title_lower for keyword in ['release', 'version', 'v6.', 'v7.', 'v8.']):
            return 'release'
        
        # Check labels
        if any('bug' in label for label in labels):
            return 'bug'
        
        if any(label in labels for label in ['feature', 'enhancement']):
            return 'feature'
        
        if any('question' in label for label in labels):
            return 'question'
        
        if any(label in labels for label in ['documentation', 'docs']):
            return 'documentation'
        
        return 'other'
    
    def classify_audience(self, issue: Dict, issue_type: str) -> str:
        """
        Classify issue audience: internal or external.
        
        Args:
            issue: Issue dictionary
            issue_type: Classified issue type
            
        Returns:
            Audience: 'internal' or 'external'
        """
        # Internal indicators
        internal_types = {'merge', 'release'}
        
        if issue_type in internal_types:
            return 'internal'
        
        title_lower = issue.get('title', '').lower()
        internal_keywords = [
            'chore', 'ci', 'cd', 'pipeline', 'workflow', 
            'audit', 'dependency', 'bump', 'yarn', 'npm',
            'build', 'deploy', 'infrastructure'
        ]
        
        if any(keyword in title_lower for keyword in internal_keywords):
            return 'internal'
        
        # Check if it's a maintenance/chore label
        labels = [label['name'].lower() for label in issue.get('labels', [])]
        if any(label in labels for label in ['chore', 'maintenance', 'dependencies']):
            return 'internal'
        
        # Check comment count - internal issues often have fewer comments
        comment_count = issue.get('comments', 0)
        if comment_count == 0 and issue_type in {'merge', 'release'}:
            return 'internal'
        
        # Default to external for user-facing issues
        return 'external'
    
    def determine_context(self, issue: Dict, issue_type: str) -> str:
        """
        Determine issue context.
        
        Args:
            issue: Issue dictionary
            issue_type: Classified issue type
            
        Returns:
            Context: 'development', 'ci_cd', 'production', 'documentation'
        """
        title_lower = issue.get('title', '').lower()
        
        # CI/CD indicators
        ci_cd_keywords = ['ci', 'cd', 'pipeline', 'workflow', 'build', 'deploy', 'test']
        if any(keyword in title_lower for keyword in ci_cd_keywords):
            return 'ci_cd'
        
        # Documentation indicators
        doc_keywords = ['docs', 'documentation', 'readme', 'guide']
        if any(keyword in title_lower for keyword in doc_keywords):
            return 'documentation'
        
        # Development indicators
        dev_keywords = ['merge', 'branch', 'pr', 'development', 'dev']
        if issue_type in {'merge', 'release'} or any(keyword in title_lower for keyword in dev_keywords):
            return 'development'
        
        # Production issues
        prod_keywords = ['production', 'prod', 'user', 'customer']
        if any(keyword in title_lower for keyword in prod_keywords):
            return 'production'
        
        return 'development'  # Default
    
    def convert_issue_to_qa(self, issue: Dict, comments: Optional[List[Dict]] = None) -> Optional[Dict]:
        """
        Convert a GitHub issue to Q&A format.
        
        Args:
            issue: Issue dictionary from GitHub API
            comments: Optional list of comments (will fetch if not provided)
            
        Returns:
            Q&A dictionary with content and metadata, or None if not suitable
        """
        # Skip if issue has no body or very short
        body = issue.get('body') or ''
        if len(body) < 20:
            return None
        
        # Classify issue
        issue_type = self.classify_issue_type(issue)
        audience = self.classify_audience(issue, issue_type)
        context = self.determine_context(issue, issue_type)
        
        # Fetch comments if not provided
        if comments is None:
            comments = self.fetch_issue_comments(issue['number'])
        
        # Build Q&A content
        question = self._format_question(issue)
        answer = self._format_answer(issue, comments)
        
        # Generate content
        content = self._format_qa_content(question, answer, issue, comments)
        
        # Generate metadata
        metadata = {
            'source': 'issue_qa',
            'repo_name': self.repo_name,
            'issue_number': issue['number'],
            'issue_title': issue['title'],
            'issue_url': issue['html_url'],
            'issue_type': issue_type,
            'audience': audience,
            'context': context,
            'doc_id': self._generate_doc_id(content),
            'doc_type': 'issue_qa',
            'created_at': issue['created_at'],
            'closed_at': issue.get('closed_at'),
            'comment_count': len(comments),
            'extracted_at': datetime.utcnow().isoformat(),
            'auto_generated': True,
            'generation_method': 'issue_qa_converter'
        }
        
        # Add labels (convert list to comma-separated string for ChromaDB compatibility)
        if issue.get('labels'):
            label_names = [label['name'] for label in issue['labels']]
            metadata['labels'] = ', '.join(label_names)  # ChromaDB requires str, not list
        
        return {
            'content': content,
            'metadata': metadata
        }
    
    def _format_question(self, issue: Dict) -> str:
        """Format issue as question."""
        title = issue['title']
        body = issue.get('body') or ''
        
        return f"{title}\n\n{body}"
    
    def _format_answer(self, issue: Dict, comments: List[Dict]) -> str:
        """Format answer from issue resolution/comments."""
        if not comments:
            return "This issue was closed without comments."
        
        # Take first few meaningful comments (skip very short ones)
        meaningful_comments = [
            c for c in comments[:5]  # Limit to first 5
            if len(c.get('body', '')) > 50  # Skip very short comments
        ]
        
        if not meaningful_comments:
            return "This issue was closed without detailed comments."
        
        # Use first meaningful comment as primary answer
        primary_comment = meaningful_comments[0]
        answer_parts = [primary_comment['body']]
        
        # Add additional context if available
        if len(meaningful_comments) > 1:
            answer_parts.append("\n\nAdditional discussion:")
            for comment in meaningful_comments[1:3]:  # Add 2 more max
                answer_parts.append(f"- {comment['body'][:200]}...")
        
        return '\n'.join(answer_parts)
    
    def _format_qa_content(self, question: str, answer: str, issue: Dict, comments: List[Dict]) -> str:
        """Format complete Q&A content."""
        lines = []
        
        # Header
        lines.append(f"# Issue #{issue['number']}: {issue['title']}")
        lines.append('')
        
        # Question section
        lines.append('## Question')
        lines.append('')
        lines.append(question)
        lines.append('')
        
        # Answer section
        lines.append('## Answer')
        lines.append('')
        lines.append(answer)
        lines.append('')
        
        # Metadata
        lines.append('---')
        lines.append('')
        lines.append(f"**Issue URL:** {issue['html_url']}")
        lines.append(f"**Status:** {issue['state']}")
        if issue.get('labels'):
            label_names = ', '.join(label['name'] for label in issue['labels'])
            lines.append(f"**Labels:** {label_names}")
        lines.append(f"**Comments:** {len(comments)}")
        
        return '\n'.join(lines)
    
    def _generate_doc_id(self, content: str) -> str:
        """Generate unique document ID using SHA256 hash."""
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def extract_all(self, max_issues: int = 100, min_body_length: int = 50) -> List[Dict]:
        """
        Extract Q&A pairs from all closed issues.
        
        Args:
            max_issues: Maximum number of issues to process
            min_body_length: Minimum issue body length to include
            
        Returns:
            List of Q&A dictionaries
        """
        logger.info(f"Fetching up to {max_issues} closed issues from {self.repo_name}")
        
        issues = self.fetch_closed_issues(max_issues)
        
        qa_pairs = []
        for i, issue in enumerate(issues, 1):
            logger.info(f"Processing issue {i}/{len(issues)}: #{issue['number']}")
            
            # Skip issues with very short bodies
            if len(issue.get('body') or '') < min_body_length:
                continue
            
            # Convert to Q&A
            qa = self.convert_issue_to_qa(issue)
            
            if qa:
                qa_pairs.append(qa)
            
            # Rate limiting
            if i % 10 == 0:
                time.sleep(1)
        
        logger.info(f"Extracted {len(qa_pairs)} Q&A pairs from {len(issues)} issues")
        return qa_pairs


if __name__ == '__main__':
    import os
    
    # Get GitHub token from environment if available
    github_token = os.environ.get('GITHUB_TOKEN')
    
    if not github_token:
        print("⚠️  No GITHUB_TOKEN found in environment")
        print("   API rate limit: 60 requests/hour (unauthenticated)")
        print("   Set GITHUB_TOKEN environment variable for 5000 requests/hour")
        print()
    
    converter = IssueQAConverter(
        repo_name='visa/visa-chart-components',
        github_token=github_token
    )
    
    # Extract from first 20 issues for testing
    qa_pairs = converter.extract_all(max_issues=20)
    
    print(f"\n✅ Extracted {len(qa_pairs)} Q&A pairs")
    
    # Save to file
    output_path = Path(__file__).parent.parent / 'data' / 'raw' / 'visa_issue_qa.json'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(qa_pairs, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Saved to: {output_path}")
    
    # Show statistics
    if qa_pairs:
        issue_types = {}
        audiences = {}
        contexts = {}
        
        for qa in qa_pairs:
            meta = qa['metadata']
            issue_types[meta['issue_type']] = issue_types.get(meta['issue_type'], 0) + 1
            audiences[meta['audience']] = audiences.get(meta['audience'], 0) + 1
            contexts[meta['context']] = contexts.get(meta['context'], 0) + 1
        
        print("\n📊 Statistics:")
        print(f"   Issue types: {dict(issue_types)}")
        print(f"   Audiences: {dict(audiences)}")
        print(f"   Contexts: {dict(contexts)}")
        
        # Show sample
        print(f"\n📄 Sample Q&A (first):")
        sample = qa_pairs[0]
        print(f"   Issue: #{sample['metadata']['issue_number']} - {sample['metadata']['issue_title']}")
        print(f"   Type: {sample['metadata']['issue_type']}")
        print(f"   Audience: {sample['metadata']['audience']}")
        print(f"   Context: {sample['metadata']['context']}")
        print(f"   Content preview: {sample['content'][:200]}...")
