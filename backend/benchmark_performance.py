#!/usr/bin/env python3
"""
Performance Benchmark Script for RAG Platform Document Processing

This script compares the performance of the original vs optimized document processing.
"""

import asyncio
import time
import sys
from pathlib import Path
from typing import List
from concurrent.futures import ProcessPoolExecutor

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from document_processor import DocumentProcessor
from document_processor_optimized import OptimizedDocumentProcessor


def process_documents_sequential(files: List[Path], processor) -> tuple:
    """Process documents sequentially (original method)"""
    start_time = time.time()
    
    total_chunks = 0
    successful = 0
    
    for file_path in files:
        try:
            chunks = processor.process_document(str(file_path))
            if chunks:
                total_chunks += len(chunks)
                successful += 1
        except Exception as e:
            print(f"Error processing {file_path.name}: {e}")
    
    elapsed = time.time() - start_time
    return total_chunks, successful, elapsed


async def process_documents_parallel(files: List[Path], processor) -> tuple:
    """Process documents in parallel (optimized method)"""
    start_time = time.time()
    
    loop = asyncio.get_event_loop()
    
    # Process documents in parallel
    with ProcessPoolExecutor(max_workers=min(4, len(files))) as executor:
        futures = [
            loop.run_in_executor(
                executor,
                processor.process_document,
                str(file_path)
            )
            for file_path in files
        ]
        
        results = await asyncio.gather(*futures, return_exceptions=True)
    
    total_chunks = 0
    successful = 0
    
    for result in results:
        if isinstance(result, Exception):
            continue
        if result:
            total_chunks += len(result)
            successful += 1
    
    elapsed = time.time() - start_time
    return total_chunks, successful, elapsed


async def run_benchmark():
    """Run performance benchmark"""
    print("=" * 80)
    print("RAG PLATFORM DOCUMENT PROCESSING PERFORMANCE BENCHMARK")
    print("=" * 80)
    print()
    
    # Get files to process
    files_dir = Path(__file__).parent.parent / "files"
    supported_extensions = ['.pdf', '.docx', '.doc', '.xlsx', '.xls', '.odt', '.txt', '.md', '.json', '.csv']
    files = [f for f in files_dir.rglob('*') if f.suffix.lower() in supported_extensions]
    
    if not files:
        print("❌ No files found in /app/files directory")
        return
    
    print(f"📁 Found {len(files)} documents to process:")
    for f in files:
        file_size_kb = f.stat().st_size / 1024
        print(f"   - {f.name} ({file_size_kb:.1f} KB)")
    print()
    
    # Test 1: Original Sequential Processing
    print("🔄 Test 1: Original Sequential Processing")
    print("-" * 80)
    original_processor = DocumentProcessor()
    
    chunks_orig, success_orig, time_orig = process_documents_sequential(
        files, original_processor
    )
    
    print(f"✅ Results:")
    print(f"   - Files processed: {success_orig}/{len(files)}")
    print(f"   - Total chunks: {chunks_orig}")
    print(f"   - Time: {time_orig:.2f} seconds")
    print(f"   - Speed: {chunks_orig/time_orig:.2f} chunks/sec")
    print()
    
    # Small delay between tests
    await asyncio.sleep(1)
    
    # Test 2: Optimized Parallel Processing
    print("⚡ Test 2: Optimized Parallel Processing")
    print("-" * 80)
    optimized_processor = OptimizedDocumentProcessor()
    
    chunks_opt, success_opt, time_opt = await process_documents_parallel(
        files, optimized_processor
    )
    
    print(f"✅ Results:")
    print(f"   - Files processed: {success_opt}/{len(files)}")
    print(f"   - Total chunks: {chunks_opt}")
    print(f"   - Time: {time_opt:.2f} seconds")
    print(f"   - Speed: {chunks_opt/time_opt:.2f} chunks/sec")
    print()
    
    # Calculate speedup
    print("=" * 80)
    print("📊 PERFORMANCE COMPARISON")
    print("=" * 80)
    print()
    
    if time_orig > 0 and time_opt > 0:
        speedup = time_orig / time_opt
        time_saved = time_orig - time_opt
        percent_faster = ((time_orig - time_opt) / time_orig) * 100
        
        print(f"⚡ Speedup: {speedup:.2f}x faster")
        print(f"⏱️  Time saved: {time_saved:.2f} seconds ({percent_faster:.1f}% faster)")
        print()
        
        if chunks_orig == chunks_opt:
            print("✅ Accuracy: PERFECT - Same number of chunks extracted")
        else:
            print(f"⚠️  Accuracy: {chunks_opt}/{chunks_orig} chunks ({100*chunks_opt/chunks_orig:.1f}%)")
        print()
        
        # Extrapolate for larger datasets
        print("📈 Estimated Performance for Larger Datasets:")
        print("-" * 80)
        
        datasets = [10, 50, 100, 500, 1000]
        for num_docs in datasets:
            orig_time = (time_orig / len(files)) * num_docs
            opt_time = (time_opt / len(files)) * num_docs
            saved = orig_time - opt_time
            
            print(f"   {num_docs:4d} documents:")
            print(f"      Original: {orig_time:7.1f}s | Optimized: {opt_time:6.1f}s | Saved: {saved:6.1f}s ({saved/60:.1f} min)")
        
        print()
        print("=" * 80)
        print(f"🎯 OPTIMIZATION ACHIEVED: {speedup:.2f}x FASTER PROCESSING!")
        print("=" * 80)
    else:
        print("⚠️  Could not calculate speedup (times too short)")


if __name__ == "__main__":
    asyncio.run(run_benchmark())
