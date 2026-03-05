#!/usr/bin/env python3
"""
Collection Rename Script: fastapi_docs → vcc_docs

This script safely renames the ChromaDB collection from the misleading
'fastapi_docs' name to the correct 'vcc_docs' name.

Usage:
    python rename_collection.py [--verify-only]

Options:
    --verify-only: Only verify the collection without making changes
"""

import chromadb
import argparse
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

def verify_collection(client: chromadb.ClientAPI, collection_name: str):
    """Verify collection exists and contains VCC data"""
    try:
        collection = client.get_collection(collection_name)
        count = collection.count()
        
        # Sample metadata to verify it's VCC data
        sample = collection.get(limit=10, include=['metadatas'])
        repo_names = set(m.get('repo_name', 'unknown') for m in sample['metadatas'])
        
        print(f"\n{'='*60}")
        print(f"Collection: {collection_name}")
        print(f"{'='*60}")
        print(f"  Document count: {count}")
        print(f"  Repository names: {repo_names}")
        print(f"{'='*60}\n")
        
        # Verify it's VCC data
        if 'visa/visa-chart-components' not in repo_names:
            print("⚠️  WARNING: Collection may not contain VCC data!")
            return False
        
        if count != 2696:
            print(f"⚠️  WARNING: Expected 2696 documents, found {count}")
            return False
        
        print("✓ Collection verified as VCC data")
        return True
        
    except ValueError:
        print(f"❌ Collection '{collection_name}' does not exist")
        return False


def rename_collection(
    client: chromadb.ClientAPI,
    old_name: str,
    new_name: str,
    delete_old: bool = False
):
    """
    Rename a ChromaDB collection by creating a new collection and copying data
    
    Args:
        client: ChromaDB client
        old_name: Current collection name
        new_name: Desired collection name
        delete_old: Whether to delete the old collection after copying
    """
    print(f"\n🔄 Renaming collection: {old_name} → {new_name}")
    print("="*60)
    
    # Step 1: Verify old collection
    print(f"\n[1/5] Verifying old collection '{old_name}'...")
    if not verify_collection(client, old_name):
        print("❌ Verification failed. Aborting.")
        return False
    
    # Step 2: Check if new collection already exists
    print(f"\n[2/5] Checking if '{new_name}' already exists...")
    try:
        existing = client.get_collection(new_name)
        print(f"⚠️  Collection '{new_name}' already exists with {existing.count()} documents")
        
        response = input("Do you want to DELETE and recreate it? (yes/no): ")
        if response.lower() != 'yes':
            print("❌ Aborted by user")
            return False
        
        client.delete_collection(new_name)
        print(f"✓ Deleted existing '{new_name}' collection")
    except ValueError:
        print(f"✓ Collection '{new_name}' does not exist (safe to create)")
    
    # Step 3: Get all data from old collection
    print(f"\n[3/5] Fetching all data from '{old_name}'...")
    old_collection = client.get_collection(old_name)
    
    # Get data in batches to avoid memory issues
    batch_size = 1000
    total_docs = old_collection.count()
    
    print(f"  Total documents to copy: {total_docs}")
    print(f"  Batch size: {batch_size}")
    
    # Create new collection
    print(f"\n[4/5] Creating new collection '{new_name}'...")
    new_collection = client.create_collection(
        name=new_name,
        metadata={
            "description": "Visa Chart Components documentation",
            "source": "visa/visa-chart-components",
            "migrated_from": old_name,
            "document_count": total_docs
        }
    )
    print(f"✓ Created collection '{new_name}'")
    
    # Copy data in batches
    print(f"\n[5/5] Copying data in batches...")
    offset = 0
    copied = 0
    
    while offset < total_docs:
        # Calculate batch size (handle last batch)
        current_batch_size = min(batch_size, total_docs - offset)
        
        # Get batch data
        batch_data = old_collection.get(
            limit=current_batch_size,
            offset=offset,
            include=['documents', 'metadatas', 'embeddings']
        )
        
        # Add to new collection
        if batch_data['ids']:
            new_collection.add(
                ids=batch_data['ids'],
                documents=batch_data['documents'],
                metadatas=batch_data['metadatas'],
                embeddings=batch_data['embeddings']
            )
            copied += len(batch_data['ids'])
            
            # Progress indicator
            progress = (copied / total_docs) * 100
            print(f"  Progress: {copied}/{total_docs} ({progress:.1f}%)", end='\r')
        
        offset += current_batch_size
    
    print(f"\n✓ Copied {copied} documents successfully")
    
    # Verify new collection
    print(f"\nVerifying new collection...")
    if not verify_collection(client, new_name):
        print("❌ Verification failed!")
        return False
    
    # Delete old collection if requested
    if delete_old:
        print(f"\n⚠️  Deleting old collection '{old_name}'...")
        response = input("Are you SURE you want to delete the old collection? (yes/no): ")
        if response.lower() == 'yes':
            client.delete_collection(old_name)
            print(f"✓ Deleted old collection '{old_name}'")
        else:
            print(f"✓ Kept old collection '{old_name}' as backup")
    else:
        print(f"\n✓ Kept old collection '{old_name}' as backup")
        print(f"   (You can delete it manually later if everything works)")
    
    print(f"\n{'='*60}")
    print(f"✅ SUCCESS: Collection renamed to '{new_name}'")
    print(f"{'='*60}")
    print(f"\n📝 Next steps:")
    print(f"   1. Update backend/.env: CHROMA_COLLECTION_NAME={new_name}")
    print(f"   2. Restart backend server")
    print(f"   3. Test query endpoint")
    print(f"   4. Delete old collection if everything works")
    
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Rename ChromaDB collection from fastapi_docs to vcc_docs"
    )
    parser.add_argument(
        '--verify-only',
        action='store_true',
        help='Only verify the collection without making changes'
    )
    parser.add_argument(
        '--delete-old',
        action='store_true',
        help='Delete old collection after successful rename'
    )
    parser.add_argument(
        '--db-path',
        type=str,
        default='./data/chroma_db',
        help='Path to ChromaDB database (default: ./data/chroma_db)'
    )
    
    args = parser.parse_args()
    
    # Initialize ChromaDB client
    print(f"🔌 Connecting to ChromaDB at: {args.db_path}")
    client = chromadb.PersistentClient(path=args.db_path)
    
    if args.verify_only:
        print("\n🔍 VERIFY-ONLY MODE (no changes will be made)")
        verify_collection(client, 'fastapi_docs')
        
        # Check if vcc_docs already exists
        try:
            verify_collection(client, 'vcc_docs')
        except:
            print("ℹ️  Collection 'vcc_docs' does not exist yet")
        
        return 0
    
    # Perform rename
    success = rename_collection(
        client=client,
        old_name='fastapi_docs',
        new_name='vcc_docs',
        delete_old=args.delete_old
    )
    
    return 0 if success else 1


if __name__ == '__main__':
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
