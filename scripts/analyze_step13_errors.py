import json
from pathlib import Path
from collections import defaultdict

def calculate_metrics(traces, classes):
    if not traces:
        return {}
    
    y_true = [t["expected_trust_state"] for t in traces]
    y_pred = [t["actual_trust_state"] for t in traces]
    
    correct = sum(1 for yt, yp in zip(y_true, y_pred) if yt == yp)
    accuracy = correct / len(traces)
    
    class_metrics = {}
    for cls in classes:
        tp = sum(1 for yt, yp in zip(y_true, y_pred) if yt == cls and yp == cls)
        fp = sum(1 for yt, yp in zip(y_true, y_pred) if yt != cls and yp == cls)
        fn = sum(1 for yt, yp in zip(y_true, y_pred) if yt == cls and yp != cls)
        support = sum(1 for yt in y_true if yt == cls)
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else (0.0 if support > 0 else None)
        recall = tp / (tp + fn) if (tp + fn) > 0 else (0.0 if support > 0 else None)
        f1 = 2 * (precision * recall) / (precision + recall) if precision and recall else (0.0 if support > 0 else None)
        
        class_metrics[cls] = {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "support": support
        }
    
    # Macro avg (ignoring classes with 0 support)
    supported_classes = [c for c in classes if class_metrics[c]["support"] > 0]
    macro_p = sum(class_metrics[c]["precision"] for c in supported_classes) / len(supported_classes) if supported_classes else 0.0
    macro_r = sum(class_metrics[c]["recall"] for c in supported_classes) / len(supported_classes) if supported_classes else 0.0
    macro_f1 = sum(class_metrics[c]["f1"] for c in supported_classes) / len(supported_classes) if supported_classes else 0.0
    
    # Compute Exact Latency (mean, median, p95)
    latencies = [t["latency"] for t in traces if "latency" in t]
    latencies.sort()
    n_lat = len(latencies)
    if n_lat > 0:
        mean_lat = sum(latencies) / n_lat
        median_lat = latencies[n_lat // 2]
        p95_idx = int(0.95 * n_lat)
        p95_lat = latencies[p95_idx]
    else:
        mean_lat, median_lat, p95_lat = 0, 0, 0
        
    return {
        "accuracy": accuracy,
        "macro_precision": macro_p,
        "macro_recall": macro_r,
        "macro_f1": macro_f1,
        "class_metrics": class_metrics,
        "latency_mean_ms": mean_lat * 1000,
        "latency_median_ms": median_lat * 1000,
        "latency_p95_ms": p95_lat * 1000
    }

def attribute_error(trace):
    expected = trace["expected_trust_state"]
    actual = trace["actual_trust_state"]
    
    if expected == actual:
        return None
        
    retrieved = trace["retrieved_notices"]
    if not retrieved:
        return "RETRIEVAL_MISS"
        
    # Check if target notice is in top 1 (we assume benchmark_case_id has format nID_vID_...)
    parts = trace["benchmark_case_id"].split("_")
    target_n = int(parts[0][1:])
    target_v = int(parts[1][1:])
    
    top_notice = retrieved[0]
    if top_notice["notice_id"] != target_n or top_notice["version_id"] != target_v:
        # Was it in the retrieved list at all?
        if any(r["notice_id"] == target_n and r["version_id"] == target_v for r in retrieved):
            return "WRONG_NOTICE_RANKED"
        return "RETRIEVAL_MISS"
    
    # If the right chunk is retrieved but we got INSUFFICIENT_EVIDENCE
    if actual == "INSUFFICIENT_EVIDENCE":
        reason = trace.get("abstention_reason")
        if reason == "UNSUPPORTED_CLAIM_FIELD":
            if trace["expected_trust_state"] != "INSUFFICIENT_EVIDENCE":
                return "CLAIM_DECOMPOSITION_FAILURE"
        if reason == "NO_OFFICIAL_FIELD" or reason == "INSUFFICIENT_FIELD_COVERAGE":
            return "STRUCTURED_COVERAGE_GAP"
        return "ABSTENTION_POLICY"
        
    # If we have CONFLICT instead of VERIFIED, or VERIFIED instead of CONFLICT
    # Check field comparison states
    field_states = trace["field_comparison_states"]
    for field, state in field_states.items():
        if state == "CONFLICT" and expected == "VERIFIED":
            # the comparator thought it conflicted but we expected verified
            if field == "deadline": return "DATE_NORMALIZATION_FAILURE"
            if field == "action": return "ACTION_NORMALIZATION_FAILURE"
            if field == "location": return "LOCATION_MATCHING_FAILURE"
            if field == "audience": return "AUDIENCE_MATCHING_FAILURE"
            return f"{field.upper()}_MATCHING_FAILURE"
            
    # Default fallback
    return "OTHER"

def main():
    step13_dir = Path("data/benchmark/step13")
    
    traces = []
    with open(step13_dir / "evaluation_traces.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                traces.append(json.loads(line))
                
    controlled_traces = [t for t in traces if t["set_name"] == "controlled_synthetic"]
    source_traces = [t for t in traces if t["set_name"] == "source_derived"]
    
    classes = ["VERIFIED", "PARTIALLY_VERIFIED", "CONFLICT", "INSUFFICIENT_EVIDENCE"]
    
    controlled_metrics = calculate_metrics(controlled_traces, classes)
    source_metrics = calculate_metrics(source_traces, classes)
    
    # Update verification_metrics.json
    metrics_path = step13_dir / "verification_metrics.json"
    with open(metrics_path, "r", encoding="utf-8") as f:
        metrics_data = json.load(f)
        
    metrics_data["controlled_synthetic_benchmark"] = {
        "population_name": "CONTROLLED SYNTHETIC BENCHMARK DERIVED FROM HUMAN-REVIEWED DUT EVIDENCE",
        "N": len(controlled_traces),
        "metrics": controlled_metrics
    }
    
    metrics_data["source_derived_claim_set"] = {
        "population_name": "REVIEWED SOURCE-DERIVED CLAIM SET",
        "N": len(source_traces),
        "metrics": source_metrics
    }
    
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics_data, f, indent=2)
        
    # Field-level metrics
    field_counts = defaultdict(lambda: {"correct": 0, "incorrect": 0})
    for t in traces:
        states = t.get("field_comparison_states", {})
        expected = t["expected_trust_state"]
        for f, state in states.items():
            # For exact-match fields, if expected is VERIFIED, we want MATCH.
            # If expected is CONFLICT, we want CONFLICT.
            if expected == "VERIFIED":
                if state == "MATCH":
                    field_counts[f]["correct"] += 1
                else:
                    field_counts[f]["incorrect"] += 1
            elif expected == "CONFLICT" and t.get("mutated_field") == f:
                if state == "CONFLICT":
                    field_counts[f]["correct"] += 1
                else:
                    field_counts[f]["incorrect"] += 1
            elif expected == "CONFLICT" and t.get("mutated_field") != f:
                # Other unmutated fields should still MATCH
                if state == "MATCH":
                    field_counts[f]["correct"] += 1
                else:
                    field_counts[f]["incorrect"] += 1

    field_metrics = {}
    for f, counts in field_counts.items():
        n = counts["correct"] + counts["incorrect"]
        acc = counts["correct"] / n if n > 0 else 0
        field_metrics[f] = {
            "N": n,
            "correct": counts["correct"],
            "incorrect": counts["incorrect"],
            "accuracy": acc
        }
    
    with open(step13_dir / "field_metrics.json", "w", encoding="utf-8") as f:
        json.dump(field_metrics, f, indent=2)
        
    # Error Analysis
    error_cases = []
    taxonomy_counts = defaultdict(int)
    
    for t in traces:
        err = attribute_error(t)
        if err:
            taxonomy_counts[err] += 1
            t["attributed_error"] = err
            error_cases.append(t)
            
    with open(step13_dir / "error_analysis.json", "w", encoding="utf-8") as f:
        json.dump({
            "total_errors": len(error_cases),
            "taxonomy_distribution": taxonomy_counts
        }, f, indent=2)
        
    with open(step13_dir / "error_cases.jsonl", "w", encoding="utf-8") as f:
        for ec in error_cases:
            f.write(json.dumps(ec, ensure_ascii=False) + "\n")
            
    # Print some logs
    print(f"Metrics saved to {metrics_path}")
    print(f"Error analysis saved. {len(error_cases)} errors found.")

if __name__ == "__main__":
    main()
