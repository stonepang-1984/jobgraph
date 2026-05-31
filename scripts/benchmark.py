"""Performance benchmark script for Multimodal Graph RAG."""

import argparse
import statistics
import sys
import time
from pathlib import Path
from typing import Callable

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger


def benchmark(func: Callable, iterations: int = 10, warmup: int = 2) -> dict:
    """Benchmark a function."""
    # Warmup
    for _ in range(warmup):
        func()

    # Measure
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        result = func()
        elapsed = time.perf_counter() - start
        times.append(elapsed)

    return {
        "iterations": iterations,
        "total": sum(times),
        "mean": statistics.mean(times),
        "median": statistics.median(times),
        "min": min(times),
        "max": max(times),
        "stdev": statistics.stdev(times) if len(times) > 1 else 0,
        "p95": sorted(times)[int(len(times) * 0.95)],
        "p99": sorted(times)[int(len(times) * 0.99)],
        "last_result": result,
    }


def benchmark_embedding(query: str = "测试文本嵌入性能", iterations: int = 20) -> dict:
    """Benchmark text embedding."""
    from src.embeddings.text_embedder import text_embedder

    logger.info(f"Benchmarking text embedding ({iterations} iterations)...")

    def run():
        return text_embedder.embed(query)

    result = benchmark(run, iterations)
    result["dimension"] = len(result["last_result"])
    return result


def benchmark_vector_retrieval(query: str = "测试查询", iterations: int = 20) -> dict:
    """Benchmark vector retrieval."""
    from src.retrieval.vector_retriever import vector_retriever

    logger.info(f"Benchmarking vector retrieval ({iterations} iterations)...")

    def run():
        return vector_retriever.retrieve(query, top_k=10)

    result = benchmark(run, iterations)
    result["result_count"] = len(result["last_result"])
    return result


def benchmark_graph_retrieval(entity: str = "测试实体", iterations: int = 20) -> dict:
    """Benchmark graph retrieval."""
    from src.retrieval.graph_retriever import graph_retriever

    logger.info(f"Benchmarking graph retrieval ({iterations} iterations)...")

    def run():
        return graph_retriever.retrieve_by_entity([entity])

    result = benchmark(run, iterations)
    result["result_count"] = len(result["last_result"])
    return result


def benchmark_hybrid_retrieval(query: str = "测试混合检索", iterations: int = 10) -> dict:
    """Benchmark hybrid retrieval."""
    from src.retrieval.hybrid_retriever import hybrid_retriever

    logger.info(f"Benchmarking hybrid retrieval ({iterations} iterations)...")

    def run():
        return hybrid_retriever.retrieve(query, top_k=10)

    result = benchmark(run, iterations)
    result["result_count"] = len(result["last_result"])
    return result


def benchmark_full_query(question: str = "这是一个测试问题", iterations: int = 5) -> dict:
    """Benchmark full query pipeline (retrieval + generation)."""
    from src.retrieval.hybrid_retriever import query_engine

    logger.info(f"Benchmarking full query ({iterations} iterations)...")

    def run():
        return query_engine.query(question)

    result = benchmark(run, iterations)
    result["answer_length"] = len(result["last_result"].get("answer", ""))
    return result


def benchmark_neo4j_connection(iterations: int = 50) -> dict:
    """Benchmark Neo4j connection and simple query."""
    from src.graph.neo4j_client import neo4j_client

    logger.info(f"Benchmarking Neo4j connection ({iterations} iterations)...")

    def run():
        return neo4j_client.execute_query("MATCH (n) RETURN count(n) AS count LIMIT 1")

    return benchmark(run, iterations)


def print_results(name: str, results: dict) -> None:
    """Print benchmark results."""
    print(f"\n{'='*60}")
    print(f"📊 {name}")
    print(f"{'='*60}")
    print(f"  迭代次数: {results['iterations']}")
    print(f"  总耗时:   {results['total']:.3f}s")
    print(f"  平均耗时: {results['mean']*1000:.2f}ms")
    print(f"  中位数:   {results['median']*1000:.2f}ms")
    print(f"  最小耗时: {results['min']*1000:.2f}ms")
    print(f"  最大耗时: {results['max']*1000:.2f}ms")
    print(f"  标准差:   {results['stdev']*1000:.2f}ms")
    print(f"  P95:      {results['p95']*1000:.2f}ms")
    print(f"  P99:      {results['p99']*1000:.2f}ms")

    # Print extra info
    for key in ["dimension", "result_count", "answer_length"]:
        if key in results:
            print(f"  {key}: {results[key]}")


def run_all_benchmarks(iterations: int = 10) -> dict:
    """Run all benchmarks."""
    all_results = {}

    benchmarks = [
        ("Neo4j Connection", lambda: benchmark_neo4j_connection(iterations * 5)),
        ("Text Embedding", lambda: benchmark_embedding(iterations=iterations * 2)),
        ("Vector Retrieval", lambda: benchmark_vector_retrieval(iterations=iterations * 2)),
        ("Graph Retrieval", lambda: benchmark_graph_retrieval(iterations=iterations * 2)),
        ("Hybrid Retrieval", lambda: benchmark_hybrid_retrieval(iterations=iterations)),
        ("Full Query Pipeline", lambda: benchmark_full_query(iterations=max(3, iterations // 2))),
    ]

    for name, bench_func in benchmarks:
        try:
            logger.info(f"\nRunning: {name}")
            results = bench_func()
            all_results[name] = results
            print_results(name, results)
        except Exception as e:
            logger.error(f"{name} failed: {e}")
            all_results[name] = {"error": str(e)}

    return all_results


def main():
    parser = argparse.ArgumentParser(description="Performance benchmark")
    parser.add_argument(
        "--benchmark", "-b",
        choices=["all", "embedding", "vector", "graph", "hybrid", "query", "neo4j"],
        default="all",
        help="Benchmark to run",
    )
    parser.add_argument(
        "--iterations", "-n",
        type=int,
        default=10,
        help="Number of iterations",
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        help="Output file for results (JSON)",
    )
    args = parser.parse_args()

    # Configure logging
    logger.remove()
    logger.add(sys.stderr, level="INFO")

    print("\n" + "=" * 60)
    print("🚀 Multimodal Graph RAG - Performance Benchmark")
    print("=" * 60)

    # Run benchmarks
    if args.benchmark == "all":
        results = run_all_benchmarks(args.iterations)
    elif args.benchmark == "embedding":
        results = {"Text Embedding": benchmark_embedding(iterations=args.iterations)}
        print_results("Text Embedding", results["Text Embedding"])
    elif args.benchmark == "vector":
        results = {"Vector Retrieval": benchmark_vector_retrieval(iterations=args.iterations)}
        print_results("Vector Retrieval", results["Vector Retrieval"])
    elif args.benchmark == "graph":
        results = {"Graph Retrieval": benchmark_graph_retrieval(iterations=args.iterations)}
        print_results("Graph Retrieval", results["Graph Retrieval"])
    elif args.benchmark == "hybrid":
        results = {"Hybrid Retrieval": benchmark_hybrid_retrieval(iterations=args.iterations)}
        print_results("Hybrid Retrieval", results["Hybrid Retrieval"])
    elif args.benchmark == "query":
        results = {"Full Query Pipeline": benchmark_full_query(iterations=args.iterations)}
        print_results("Full Query Pipeline", results["Full Query Pipeline"])
    elif args.benchmark == "neo4j":
        results = {"Neo4j Connection": benchmark_neo4j_connection(iterations=args.iterations)}
        print_results("Neo4j Connection", results["Neo4j Connection"])

    # Save results
    if args.output:
        import json

        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert results for JSON serialization
        serializable = {}
        for name, result in results.items():
            serializable[name] = {
                k: v for k, v in result.items()
                if k != "last_result"
            }

        with open(output_path, "w") as f:
            json.dump(serializable, f, indent=2, ensure_ascii=False)

        print(f"\n结果已保存到: {output_path}")

    print("\n" + "=" * 60)
    print("✅ Benchmark 完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
