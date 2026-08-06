import os
import time
import fitz  # PyMuPDF
from app.services.knowledge_service import knowledge_service

def generate_sample_pdf(filepath: str):
    """
    Generate a sample multi-page engineering syllabus & notes PDF document.
    """
    doc = fitz.open()

    # Page 1: Data Structures - Binary Search Trees
    page1 = doc.new_page()
    page1.insert_text((50, 50), "CS301: Data Structures & Algorithms\nUnit 1: Tree Data Structures", fontsize=16)
    page1.insert_text((50, 100), 
        "A Binary Search Tree (BST) is a node-based binary tree data structure which has the following properties:\n"
        "- The left subtree of a node contains only nodes with keys lesser than the node's key.\n"
        "- The right subtree of a node contains only nodes with keys greater than the node's key.\n"
        "- The left and right subtree each must also be a binary search tree.\n\n"
        "Basic operations on a BST include Search, Insertion, Deletion, and Inorder Traversal.\n"
        "The average time complexity for searching in a BST is O(log n), whereas the worst-case complexity is O(n) for skewed trees.",
        fontsize=11
    )

    # Page 2: Sorting Algorithms - QuickSort
    page2 = doc.new_page()
    page2.insert_text((50, 50), "CS301: Data Structures & Algorithms\nUnit 2: Divide and Conquer Sorting Algorithms", fontsize=16)
    page2.insert_text((50, 100),
        "QuickSort is a Divide and Conquer algorithm. It picks an element as pivot and partitions the given array around the picked pivot.\n"
        "There are many different versions of QuickSort that pick pivot in different ways:\n"
        "1. Always pick first element as pivot.\n"
        "2. Always pick last element as pivot.\n"
        "3. Pick a random element as pivot.\n\n"
        "Time Complexity Analysis of QuickSort:\n"
        "- Best Case: O(n log n)\n"
        "- Average Case: O(n log n)\n"
        "- Worst Case: O(n^2) when array is already sorted and first/last element is picked as pivot.\n"
        "Space Complexity is O(log n) due to recursive call stack.",
        fontsize=11
    )

    # Page 3: Graph Algorithms - BFS and DFS
    page3 = doc.new_page()
    page3.insert_text((50, 50), "CS301: Data Structures & Algorithms\nUnit 3: Graph Traversals", fontsize=16)
    page3.insert_text((50, 100),
        "Graph Traversal algorithms explore vertices and edges in a graph structure.\n"
        "1. Breadth-First Search (BFS):\n"
        "BFS explores graph level by level starting from a source node using a Queue (FIFO) data structure. "
        "Time complexity is O(V + E) where V is vertices and E is edges.\n\n"
        "2. Depth-First Search (DFS):\n"
        "DFS explores as deep as possible along each branch before backtracking using a Stack (LIFO) or Recursion. "
        "Time complexity is O(V + E).\n"
        "BFS is used for shortest path in unweighted graphs, while DFS is useful for topological sorting and cycle detection.",
        fontsize=11
    )

    doc.save(filepath)
    doc.close()
    print(f"Generated sample PDF at '{filepath}' with 3 pages.")

def main():
    print("=" * 70)
    print("VivaBot Phase 1 Knowledge Base Test Script")
    print("=" * 70)

    sample_pdf_path = "sample_data_structures_notes.pdf"
    generate_sample_pdf(sample_pdf_path)

    # Read PDF bytes
    with open(sample_pdf_path, "rb") as f:
        pdf_bytes = f.read()

    print("\n--- STEP 1: Uploading & Ingesting PDF Document ---")
    upload_res = knowledge_service.process_and_index_document(
        file_bytes=pdf_bytes,
        filename=sample_pdf_path,
        subject="Data Structures & Algorithms",
        topic="Computer Science Unit 1-3"
    )
    print(f"Status: {upload_res['status']}")
    print(f"Ingested Pages: {upload_res['total_pages']}")
    print(f"Generated Chunks: {upload_res['total_chunks']}")
    print(f"Processing & Indexing Latency: {upload_res['processing_latency_ms']} ms")

    # Step 2: Ask 3 queries and show retrieved chunks + latency
    queries = [
        "What is a Binary Search Tree and what are its operations?",
        "Explain the time complexity of QuickSort algorithm.",
        "What are Graph Traversal algorithms like BFS and DFS?"
    ]

    print("\n--- STEP 2: Deterministic Semantic Search Evaluation (3 Queries) ---")
    
    total_retrieval_latency = 0.0

    for i, q in enumerate(queries, 1):
        print(f"\n[QUERY {i}]: '{q}'")
        search_res = knowledge_service.search_knowledge_base(query=q, top_k=2, subject="Data Structures & Algorithms")
        latency = search_res["retrieval_latency_ms"]
        total_retrieval_latency += latency

        print(f"Retrieval Latency: {latency} ms")
        print("Top Retrieved Chunks:")
        for idx, result in enumerate(search_res["results"], 1):
            meta = result["metadata"]
            print(f"  Result #{idx} (Similarity Score: {result['similarity_score']}):")
            print(f"    - Source: {meta['source_file']} (Page {meta['page_number']})")
            print(f"    - Chunk ID: {result['chunk_id']}")
            print(f"    - Text Snippet: \"{result['text'][:150]}...\"")
            print("-" * 50)

    avg_latency = round(total_retrieval_latency / len(queries), 2)
    print("\n" + "=" * 70)
    print("SUMMARY METRICS")
    print("=" * 70)
    print(f"Total Queries Executed: {len(queries)}")
    print(f"Average Retrieval Latency: {avg_latency} ms")
    print("Knowledge Base Storage: ChromaDB Persistent Collection (HNSW Indexed)")
    print("Embedding Model: BAAI/bge-small-en-v1.5 (384 dimensions, local inference)")
    print("=" * 70)

    # Clean up temp file
    if os.path.exists(sample_pdf_path):
        os.remove(sample_pdf_path)

if __name__ == "__main__":
    main()
