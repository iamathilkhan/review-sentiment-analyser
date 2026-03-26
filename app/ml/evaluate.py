import json
import os
import sys
import time
from collections import defaultdict
import numpy as np
from typing import List, Dict

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ml.model_loader import get_pipeline
from app.ml.fallback import FallbackPipeline
from app.ml.config import ASPECT_CATEGORIES

def evaluate():
    eval_file = os.path.join(os.path.dirname(__file__), "eval_samples.json")
    if not os.path.exists(eval_file):
        print(f"Error: Evaluation file not found at {eval_file}")
        return

    with open(eval_file, "r") as f:
        samples = json.load(f)

    print(f"Loaded {len(samples)} evaluation samples.")
    
    # Try to get the main pipeline, otherwise fallback
    try:
        pipeline = get_pipeline()
    except Exception as e:
        print(f"Main pipeline failed to load: {e}. Using FallbackPipeline.")
        pipeline = FallbackPipeline()

    results = []
    
    # Metrics containers
    # We'll track TP, FP, FN for each category and polarity
    # Also for category detection (OTE+ACD)
    metrics = {cat: {"TP": 0, "FP": 0, "FN": 0} for cat in ASPECT_CATEGORIES}
    polarity_confusion = defaultdict(lambda: defaultdict(int)) # [ground_truth][predicted]
    
    print("Running evaluation...")
    start_time = time.time()
    
    for sample in samples:
        text = sample["text"]
        gt_aspects = {a["aspect_category"]: a["polarity"] for a in sample["ground_truth"]}
        
        # Process
        prediction = pipeline.process_review(text)
        pred_aspects = {a.aspect_category: a.polarity for a in prediction.aspects}
        
        sample_result = {
            "text": text,
            "ground_truth": sample["ground_truth"],
            "predictions": [a.model_dump() for a in prediction.aspects],
            "correct": True
        }
        
        # Evaluate categories
        for cat in ASPECT_CATEGORIES:
            gt_pol = gt_aspects.get(cat)
            pred_pol = pred_aspects.get(cat)
            
            if gt_pol and pred_pol:
                # Correct detection
                metrics[cat]["TP"] += 1
                polarity_confusion[gt_pol][pred_pol] += 1
                if gt_pol != pred_pol:
                    sample_result["correct"] = False
            elif gt_pol and not pred_pol:
                # Missed aspect
                metrics[cat]["FN"] += 1
                sample_result["correct"] = False
            elif not gt_pol and pred_pol:
                # False positive
                metrics[cat]["FP"] += 1
                sample_result["correct"] = False
        
        results.append(sample_result)

    total_time = time.time() - start_time
    
    # Print Metrics
    print("\n" + "="*50)
    print("ABSA EVALUATION RESULTS")
    print("="*50)
    print(f"{'Category':<20} | {'Prec':<6} | {'Rec':<6} | {'F1':<6}")
    print("-" * 50)
    
    total_tp = 0
    total_fp = 0
    total_fn = 0
    
    for cat in ASPECT_CATEGORIES:
        tp = metrics[cat]["TP"]
        fp = metrics[cat]["FP"]
        fn = metrics[cat]["FN"]
        
        prec = tp / (tp + fp) if (tp + fp) > 0 else 0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0
        
        print(f"{cat:<20} | {prec:.4f} | {rec:.4f} | {f1:.4f}")
        
        total_tp += tp
        total_fp += fp
        total_fn += fn

    avg_prec = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0
    avg_rec = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0
    avg_f1 = 2 * avg_prec * avg_rec / (avg_prec + avg_rec) if (avg_prec + avg_rec) > 0 else 0
    
    print("-" * 50)
    print(f"{'OVERALL':<20} | {avg_prec:.4f} | {avg_rec:.4f} | {avg_f1:.4f}")
    
    print("\nPolarity Confusion Matrix (GT \\ Pred):")
    polarities = ["positive", "neutral", "negative"]
    print(f"{'':<10} | {'pos':<6} | {'neu':<6} | {'neg':<6}")
    for gt in polarities:
        row = [str(polarity_confusion[gt][p]) for p in polarities]
        print(f"{gt:<10} | {' | '.join([r.ljust(6) for r in row])}")

    print(f"\nTotal Evaluation Time: {total_time:.2f}s ({total_time/len(samples):.3f}s/sample)")
    
    # Save results
    output_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "ml_eval_results.json")
    with open(output_path, "w") as f:
        json.dump({
            "summary": {
                "precision": avg_prec,
                "recall": avg_rec,
                "f1": avg_f1,
                "samples": len(samples)
            },
            "per_category": metrics,
            "confusion_matrix": polarity_confusion,
            "detailed_results": results
        }, f, indent=2)
    print(f"\nFull results saved to: {output_path}")

if __name__ == "__main__":
    evaluate()
