"""
CS559 System Design - Automated FIO Benchmark Runner
Runs 12 experimental conditions x 3 repetitions = 36 benchmark runs.
Outputs raw JSON to raw_results/ and parsed metrics to processed_data/.
"""

import os
import sys
import json
import subprocess
import time
import pandas as pd
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIGS_DIR = os.path.join(BASE_DIR, "configs")
RAW_RESULTS_DIR = os.path.join(BASE_DIR, "raw_results")
PROCESSED_DIR = os.path.join(BASE_DIR, "processed_data")

os.makedirs(RAW_RESULTS_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)

# WSL path mapping
WSL_BASE = "/mnt/c/Users/Abhigyan Sharma/OneDrive/Desktop/FIO"
WSL_CONFIGS = f"{WSL_BASE}/configs"
WSL_RAW = f"{WSL_BASE}/raw_results"

CASES = [
    {"id": "case_a", "label": "Case A (Rand Read 4KiB 100%R)", "pattern": "randread", "bs": "4k", "mix": "100% Read"},
    {"id": "case_b", "label": "Case B (Rand R/W 4KiB 70%R/30%W)", "pattern": "randrw", "bs": "4k", "mix": "70% Read / 30% Write"},
    {"id": "case_c", "label": "Case C (Rand R/W 8KiB 30%R/70%W)", "pattern": "randrw", "bs": "8k", "mix": "30% Read / 70% Write"},
    {"id": "case_d", "label": "Case D (Seq Read 256KiB 100%R)", "pattern": "read", "bs": "256k", "mix": "100% Read"}
]

QUEUE_DEPTHS = [1, 8, 32]
REPETITIONS = 3
RUNTIME_SEC = 15
RAMP_TIME_SEC = 2

def run_wsl_command(cmd):
    full_cmd = ["wsl.exe", "-d", "Ubuntu", "-u", "root", "--", "bash", "-c", cmd]
    res = subprocess.run(full_cmd, capture_output=True, text=True)
    return res

def parse_fio_json(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    job = data["jobs"][0]
    
    read_iops = job["read"]["iops"]
    write_iops = job["write"]["iops"]
    total_iops = read_iops + write_iops
    
    # Bandwidth in MiB/s (fio reports in KiB/s)
    read_bw_mib = job["read"]["bw"] / 1024.0
    write_bw_mib = job["write"]["bw"] / 1024.0
    total_bw_mib = read_bw_mib + write_bw_mib
    
    # Latencies in microseconds (usec)
    # Total latency (lat_ns) or completion latency (clat_ns)
    # Check if clat_ns exists
    lat_data = job["read"] if job["read"]["iops"] > 0 else job["write"]
    if job["read"]["iops"] > 0 and job["write"]["iops"] > 0:
        # Weighted average for mixed workloads
        total_ios = job["read"]["total_ios"] + job["write"]["total_ios"]
        r_ios = job["read"]["total_ios"]
        w_ios = job["write"]["total_ios"]
        avg_lat_usec = (job["read"]["lat_ns"]["mean"] * r_ios + job["write"]["lat_ns"]["mean"] * w_ios) / (total_ios * 1000.0)
        avg_slat_usec = (job["read"]["slat_ns"]["mean"] * r_ios + job["write"]["slat_ns"]["mean"] * w_ios) / (total_ios * 1000.0)
        avg_clat_usec = (job["read"]["clat_ns"]["mean"] * r_ios + job["write"]["clat_ns"]["mean"] * w_ios) / (total_ios * 1000.0)
        
        # P50, P95, P99 - using clat percentiles
        # Extract from percentiles
        r_pct = job["read"]["clat_ns"]["percentile"]
        w_pct = job["write"]["clat_ns"]["percentile"]
        p50 = max(r_pct.get("50.000000", 0), w_pct.get("50.000000", 0)) / 1000.0
        p95 = max(r_pct.get("95.000000", 0), w_pct.get("95.000000", 0)) / 1000.0
        p99 = max(r_pct.get("99.000000", 0), w_pct.get("99.000000", 0)) / 1000.0
    else:
        active = job["read"] if job["read"]["iops"] > 0 else job["write"]
        avg_lat_usec = active["lat_ns"]["mean"] / 1000.0
        avg_slat_usec = active["slat_ns"]["mean"] / 1000.0
        avg_clat_usec = active["clat_ns"]["mean"] / 1000.0
        pct = active["clat_ns"]["percentile"]
        p50 = pct.get("50.000000", 0) / 1000.0
        p95 = pct.get("95.000000", 0) / 1000.0
        p99 = pct.get("99.000000", 0) / 1000.0
        
    # IO Depth achieved distribution
    io_depths = job.get("iodepth_level", {})
    
    # CPU utilization
    cpu_usr = job.get("usr_cpu", 0.0)
    cpu_sys = job.get("sys_cpu", 0.0)
    
    return {
        "read_iops": read_iops,
        "write_iops": write_iops,
        "total_iops": total_iops,
        "read_bw_mib": read_bw_mib,
        "write_bw_mib": write_bw_mib,
        "total_bw_mib": total_bw_mib,
        "avg_lat_usec": avg_lat_usec,
        "avg_slat_usec": avg_slat_usec,
        "avg_clat_usec": avg_clat_usec,
        "p50_lat_usec": p50,
        "p95_lat_usec": p95,
        "p99_lat_usec": p99,
        "cpu_usr": cpu_usr,
        "cpu_sys": cpu_sys,
        "iodepth_dist": json.dumps(io_depths)
    }

def main():
    print("=" * 80)
    print("CS559 SYSTEM DESIGN - FIO STORAGE BENCHMARK SUITE")
    print("Target file: /root/fio-lab/db-test.bin (Pre-allocated 1 GiB on ext4)")
    print(f"Configurations: 4 Cases x 3 Queue Depths x {REPETITIONS} Repetitions = {len(CASES)*len(QUEUE_DEPTHS)*REPETITIONS} Runs")
    print("=" * 80)
    
    raw_metrics_list = []
    total_runs = len(CASES) * len(QUEUE_DEPTHS) * REPETITIONS
    run_idx = 0
    start_time_all = time.time()
    
    for case in CASES:
        case_id = case["id"]
        for qd in QUEUE_DEPTHS:
            config_file = f"{WSL_CONFIGS}/{case_id}_qd{qd}.fio"
            
            for rep in range(1, REPETITIONS + 1):
                run_idx += 1
                json_filename = f"{case_id}_qd{qd}_rep{rep}.json"
                wsl_json_path = f"{WSL_RAW}/{json_filename}"
                win_json_path = os.path.join(RAW_RESULTS_DIR, json_filename)
                
                print(f"[{run_idx:02d}/{total_runs}] Running {case['label']} | QD={qd:02d} | Rep={rep} ...", end="", flush=True)
                
                cmd = f"fio '{config_file}' --runtime={RUNTIME_SEC} --ramp_time={RAMP_TIME_SEC} --output='{wsl_json_path}' --output-format=json"
                t0 = time.time()
                res = run_wsl_command(cmd)
                dur = time.time() - t0
                
                if res.returncode != 0:
                    print(f" [FAILED] (rc={res.returncode})")
                    print(f"Stderr: {res.stderr[:300]}")
                    continue
                
                # Parse JSON
                metrics = parse_fio_json(win_json_path)
                
                row = {
                    "run_id": run_idx,
                    "case_id": case_id,
                    "case_label": case["label"],
                    "pattern": case["pattern"],
                    "block_size": case["bs"],
                    "read_mix": case["mix"],
                    "queue_depth": qd,
                    "repetition": rep,
                    "duration_sec": dur,
                    **metrics
                }
                raw_metrics_list.append(row)
                
                print(f" DONE ({dur:.1f}s) | IOPS: {metrics['total_iops']:,.0f} | BW: {metrics['total_bw_mib']:.1f} MiB/s | AvgLat: {metrics['avg_lat_usec']:.1f}us | P99: {metrics['p99_lat_usec']:.1f}us")
    
    total_dur = time.time() - start_time_all
    print("=" * 80)
    print(f"ALL BENCHMARKS COMPLETED in {total_dur/60:.2f} minutes.")
    print("=" * 80)
    
    # Save raw metrics
    raw_df = pd.DataFrame(raw_metrics_list)
    raw_csv_path = os.path.join(PROCESSED_DIR, "benchmark_raw_metrics.csv")
    raw_df.to_csv(raw_csv_path, index=False)
    print(f"Raw metrics saved to: {raw_csv_path}")
    
    # Aggregate summary statistics (mean, std) across repetitions
    summary_rows = []
    grouped = raw_df.groupby(["case_id", "case_label", "pattern", "block_size", "read_mix", "queue_depth"])
    
    for (cid, clabel, pat, bs, rmix, qd), group in grouped:
        summary_rows.append({
            "case_id": cid,
            "case_label": clabel,
            "pattern": pat,
            "block_size": bs,
            "read_mix": rmix,
            "queue_depth": qd,
            "reps_count": len(group),
            "iops_mean": group["total_iops"].mean(),
            "iops_std": group["total_iops"].std(),
            "bw_mean_mib": group["total_bw_mib"].mean(),
            "bw_std_mib": group["total_bw_mib"].std(),
            "avg_lat_mean_usec": group["avg_lat_usec"].mean(),
            "avg_lat_std_usec": group["avg_lat_usec"].std(),
            "p50_mean_usec": group["p50_lat_usec"].mean(),
            "p95_mean_usec": group["p95_lat_usec"].mean(),
            "p99_mean_usec": group["p99_lat_usec"].mean(),
            "p99_std_usec": group["p99_lat_usec"].std(),
            "slat_mean_usec": group["avg_slat_usec"].mean(),
            "clat_mean_usec": group["avg_clat_usec"].mean(),
            "cpu_usr_mean": group["cpu_usr"].mean(),
            "cpu_sys_mean": group["cpu_sys"].mean()
        })
    
    summary_df = pd.DataFrame(summary_rows)
    summary_csv_path = os.path.join(PROCESSED_DIR, "benchmark_summary.csv")
    summary_df.to_csv(summary_csv_path, index=False)
    print(f"Summary statistics saved to: {summary_csv_path}")
    
    # Print formatted summary table to console
    print("\n" + "=" * 100)
    print(f"{'Case':<8} | {'QD':<4} | {'Pattern':<10} | {'BS':<6} | {'IOPS (Mean±Std)':<20} | {'BW MiB/s (Mean±Std)':<22} | {'AvgLat (us)':<12} | {'P99 (us)':<10}")
    print("-" * 100)
    for _, r in summary_df.iterrows():
        iops_str = f"{r['iops_mean']:,.0f} ± {r['iops_std']:.0f}"
        bw_str = f"{r['bw_mean_mib']:.1f} ± {r['bw_std_mib']:.1f}"
        print(f"{r['case_id']:<8} | {r['queue_depth']:<4} | {r['pattern']:<10} | {r['block_size']:<6} | {iops_str:<20} | {bw_str:<22} | {r['avg_lat_mean_usec']:<12.1f} | {r['p99_mean_usec']:<10.1f}")
    print("=" * 100)

if __name__ == "__main__":
    main()

