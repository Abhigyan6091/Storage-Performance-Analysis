"""
CS559 System Design - Plotting & Statistical Visualization
Generates 6 publication-quality figures comparing FIO storage workloads:
  Fig 1: IOPS vs Queue Depth Scaling (with error bars)
  Fig 2: Bandwidth (MiB/s) vs Queue Depth Scaling
  Fig 3: Average Latency (usec) vs Queue Depth
  Fig 4: Tail Latency (P95 and P99) vs Queue Depth
  Fig 5: Throughput vs Latency Trade-off (The Saturation Knee)
  Fig 6: Read/Write Mix & Latency Breakdown (Case B vs Case C)
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESSED_DIR = os.path.join(BASE_DIR, "processed_data")
FIGURES_DIR = os.path.join(BASE_DIR, "figures")
os.makedirs(FIGURES_DIR, exist_ok=True)

# Set high-quality visual style
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
plt.rcParams['font.sans-serif'] = 'Arial'
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.size'] = 11
plt.rcParams['axes.labelsize'] = 12
plt.rcParams['axes.titlesize'] = 13
plt.rcParams['xtick.labelsize'] = 11
plt.rcParams['ytick.labelsize'] = 11
plt.rcParams['legend.fontsize'] = 10
plt.rcParams['figure.titlesize'] = 14

CASE_COLORS = {
    "case_a": "#1f77b4",  # Steel Blue
    "case_b": "#2ca02c",  # Forest Green
    "case_c": "#d62728",  # Crimson Red
    "case_d": "#9467bd"   # Purple
}

CASE_MARKERS = {
    "case_a": "o",
    "case_b": "s",
    "case_c": "^",
    "case_d": "D"
}

CASE_LABELS = {
    "case_a": "Case A: RandRead 4KiB (100% R)",
    "case_b": "Case B: RandRW 4KiB (70% R / 30% W)",
    "case_c": "Case C: RandRW 8KiB (30% R / 70% W)",
    "case_d": "Case D: SeqRead 256KiB (100% R)"
}

def generate_plots():
    summary_path = os.path.join(PROCESSED_DIR, "benchmark_summary.csv")
    raw_path = os.path.join(PROCESSED_DIR, "benchmark_raw_metrics.csv")
    
    if not os.path.exists(summary_path):
        print(f"Error: {summary_path} not found. Run benchmarks first.")
        return
        
    df = pd.read_csv(summary_path)
    raw_df = pd.read_csv(raw_path)
    
    # -------------------------------------------------------------
    # Figure 1: IOPS vs Queue Depth
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(8, 5), dpi=300)
    for cid in ["case_a", "case_b", "case_c", "case_d"]:
        sub = df[df["case_id"] == cid].sort_values("queue_depth")
        ax.errorbar(
            sub["queue_depth"], sub["iops_mean"], yerr=sub["iops_std"],
            label=CASE_LABELS[cid], color=CASE_COLORS[cid], marker=CASE_MARKERS[cid],
            linewidth=2.2, markersize=8, capsize=4, capthick=1.5
        )
    ax.set_xscale("log", base=2)
    ax.set_xticks([1, 8, 32])
    ax.get_xaxis().set_major_formatter(ticker.ScalarFormatter())
    ax.get_yaxis().set_major_formatter(ticker.FuncFormatter(lambda x, p: f"{x:,.0f}"))
    ax.set_xlabel("Target Queue Depth (iodepth)")
    ax.set_ylabel("Total Throughput (IOPS)")
    ax.set_title("Figure 1: IOPS Scaling Across Queue Depths (Mean ± 1 SD)")
    ax.legend(frameon=True, loc="center left", bbox_to_anchor=(0.02, 0.75))
    ax.grid(True, linestyle="--", alpha=0.6)
    plt.tight_layout()
    fig1_path = os.path.join(FIGURES_DIR, "fig1_iops_scaling.png")
    plt.savefig(fig1_path)
    plt.close()
    print(f"Saved: {fig1_path}")

    # -------------------------------------------------------------
    # Figure 2: Bandwidth (MiB/s) vs Queue Depth
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(8, 5), dpi=300)
    for cid in ["case_a", "case_b", "case_c", "case_d"]:
        sub = df[df["case_id"] == cid].sort_values("queue_depth")
        ax.errorbar(
            sub["queue_depth"], sub["bw_mean_mib"], yerr=sub["bw_std_mib"],
            label=CASE_LABELS[cid], color=CASE_COLORS[cid], marker=CASE_MARKERS[cid],
            linewidth=2.2, markersize=8, capsize=4, capthick=1.5
        )
    ax.set_xscale("log", base=2)
    ax.set_xticks([1, 8, 32])
    ax.get_xaxis().set_major_formatter(ticker.ScalarFormatter())
    ax.get_yaxis().set_major_formatter(ticker.FuncFormatter(lambda x, p: f"{x:,.0f}"))
    ax.set_xlabel("Target Queue Depth (iodepth)")
    ax.set_ylabel("Total Bandwidth (MiB/s)")
    ax.set_title("Figure 2: Storage Bandwidth Scaling vs. Queue Depth")
    ax.legend(frameon=True, loc="upper left")
    ax.grid(True, linestyle="--", alpha=0.6)
    plt.tight_layout()
    fig2_path = os.path.join(FIGURES_DIR, "fig2_bandwidth_scaling.png")
    plt.savefig(fig2_path)
    plt.close()
    print(f"Saved: {fig2_path}")

    # -------------------------------------------------------------
    # Figure 3: Average Latency vs Queue Depth
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(8, 5), dpi=300)
    for cid in ["case_a", "case_b", "case_c", "case_d"]:
        sub = df[df["case_id"] == cid].sort_values("queue_depth")
        ax.errorbar(
            sub["queue_depth"], sub["avg_lat_mean_usec"], yerr=sub["avg_lat_std_usec"],
            label=CASE_LABELS[cid], color=CASE_COLORS[cid], marker=CASE_MARKERS[cid],
            linewidth=2.2, markersize=8, capsize=4, capthick=1.5
        )
    ax.set_xscale("log", base=2)
    ax.set_xticks([1, 8, 32])
    ax.get_xaxis().set_major_formatter(ticker.ScalarFormatter())
    ax.get_yaxis().set_major_formatter(ticker.FuncFormatter(lambda x, p: f"{x:,.0f} μs" if x < 1000 else f"{x/1000:.1f} ms"))
    ax.set_xlabel("Target Queue Depth (iodepth)")
    ax.set_ylabel("Average Latency (μs / ms)")
    ax.set_title("Figure 3: Average Latency Growth under Queue Buildup (Little's Law)")
    ax.legend(frameon=True, loc="upper left")
    ax.grid(True, linestyle="--", alpha=0.6)
    plt.tight_layout()
    fig3_path = os.path.join(FIGURES_DIR, "fig3_average_latency.png")
    plt.savefig(fig3_path)
    plt.close()
    print(f"Saved: {fig3_path}")

    # -------------------------------------------------------------
    # Figure 4: Tail Latency (P95 vs P99) Comparison at QD=32
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(9, 5), dpi=300)
    sub_qd32 = df[df["queue_depth"] == 32].copy()
    sub_qd32 = sub_qd32.set_index("case_id").reindex(["case_a", "case_b", "case_c", "case_d"]).reset_index()
    
    x = np.arange(len(sub_qd32))
    width = 0.25
    
    rects1 = ax.bar(x - width, sub_qd32["p50_mean_usec"], width, label="P50 (Median)", color="#4575b4", alpha=0.85)
    rects2 = ax.bar(x, sub_qd32["p95_mean_usec"], width, label="P95", color="#fdae61", alpha=0.85)
    rects3 = ax.bar(x + width, sub_qd32["p99_mean_usec"], width, label="P99 (Tail)", color="#d73027", alpha=0.85)
    
    ax.set_xticks(x)
    ax.set_xticklabels([f"Case A\n(4K 100%R)", f"Case B\n(4K 70%R)", f"Case C\n(8K 30%R)", f"Case D\n(256K Seq)"])
    ax.set_ylabel("Latency (μs)")
    ax.set_title("Figure 4: Latency Percentile Distribution (P50, P95, P99) at QD=32")
    ax.legend(frameon=True)
    ax.grid(True, linestyle="--", alpha=0.6, axis="y")
    
    # Add value annotations
    for rect in rects3:
        h = rect.get_height()
        ax.annotate(f"{h:,.0f}μs",
                    xy=(rect.get_x() + rect.get_width() / 2, h),
                    xytext=(0, 4), textcoords="offset points",
                    ha='center', va='bottom', fontsize=9, fontweight='bold')

    plt.tight_layout()
    fig4_path = os.path.join(FIGURES_DIR, "fig4_tail_latency_p99.png")
    plt.savefig(fig4_path)
    plt.close()
    print(f"Saved: {fig4_path}")

    # -------------------------------------------------------------
    # Figure 5: Throughput vs Latency Trade-Off (Knee of the Curve)
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(8, 5.5), dpi=300)
    for cid in ["case_a", "case_b", "case_c", "case_d"]:
        sub = df[df["case_id"] == cid].sort_values("queue_depth")
        ax.plot(
            sub["avg_lat_mean_usec"], sub["iops_mean"],
            label=CASE_LABELS[cid], color=CASE_COLORS[cid], marker=CASE_MARKERS[cid],
            linewidth=2.2, markersize=8
        )
        for _, row in sub.iterrows():
            ax.annotate(f"QD={int(row['queue_depth'])}",
                        xy=(row["avg_lat_mean_usec"], row["iops_mean"]),
                        xytext=(8, -4), textcoords="offset points",
                        fontsize=8, color=CASE_COLORS[cid])
                        
    ax.set_xlabel("Average Latency (μs) [Log Scale]")
    ax.set_xscale("log")
    ax.get_xaxis().set_major_formatter(ticker.FuncFormatter(lambda x, p: f"{x:,.0f} μs" if x < 1000 else f"{x/1000:.1f} ms"))
    ax.get_yaxis().set_major_formatter(ticker.FuncFormatter(lambda x, p: f"{x:,.0f}"))
    ax.set_ylabel("Throughput (IOPS)")
    ax.set_title("Figure 5: Throughput vs. Latency Trade-Off Curve (The Saturation Knee)")
    ax.legend(frameon=True, loc="upper right")
    ax.grid(True, linestyle="--", alpha=0.6)
    plt.tight_layout()
    fig5_path = os.path.join(FIGURES_DIR, "fig5_tradeoff_iops_latency.png")
    plt.savefig(fig5_path)
    plt.close()
    print(f"Saved: {fig5_path}")

    # -------------------------------------------------------------
    # Figure 6: Read vs Write Mix Comparison (Case B vs Case C)
    # -------------------------------------------------------------
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.8), dpi=300)
    
    # IOPS breakdown
    qds = [1, 8, 32]
    sub_b = df[df["case_id"] == "case_b"].sort_values("queue_depth")
    sub_c = df[df["case_id"] == "case_c"].sort_values("queue_depth")
    
    ax1.plot(sub_b["queue_depth"], sub_b["iops_mean"], 's-', color=CASE_COLORS["case_b"], label="Case B (70% Read / 4KB)", linewidth=2)
    ax1.plot(sub_c["queue_depth"], sub_c["iops_mean"], '^-', color=CASE_COLORS["case_c"], label="Case C (30% Read / 8KB)", linewidth=2)
    ax1.set_xscale("log", base=2)
    ax1.set_xticks(qds)
    ax1.get_xaxis().set_major_formatter(ticker.ScalarFormatter())
    ax1.get_yaxis().set_major_formatter(ticker.FuncFormatter(lambda x, p: f"{x:,.0f}"))
    ax1.set_xlabel("Queue Depth")
    ax1.set_ylabel("Total IOPS")
    ax1.set_title("(a) IOPS: Read-Heavy vs Write-Heavy")
    ax1.legend(frameon=True)
    ax1.grid(True, linestyle="--", alpha=0.6)
    
    # Tail Latency (P99)
    ax2.plot(sub_b["queue_depth"], sub_b["p99_mean_usec"], 's--', color=CASE_COLORS["case_b"], label="Case B P99 Latency", linewidth=2)
    ax2.plot(sub_c["queue_depth"], sub_c["p99_mean_usec"], '^--', color=CASE_COLORS["case_c"], label="Case C P99 Latency", linewidth=2)
    ax2.set_xscale("log", base=2)
    ax2.set_xticks(qds)
    ax2.get_xaxis().set_major_formatter(ticker.ScalarFormatter())
    ax2.get_yaxis().set_major_formatter(ticker.FuncFormatter(lambda x, p: f"{x:,.0f} μs"))
    ax2.set_xlabel("Queue Depth")
    ax2.set_ylabel("P99 Tail Latency (μs)")
    ax2.set_title("(b) P99 Latency: Write Penalty")
    ax2.legend(frameon=True)
    ax2.grid(True, linestyle="--", alpha=0.6)
    
    plt.suptitle("Figure 6: Comparative Analysis of Read-Heavy vs. Write-Heavy Workloads", y=1.02)
    plt.tight_layout()
    fig6_path = os.path.join(FIGURES_DIR, "fig6_read_write_mix_comparison.png")
    plt.savefig(fig6_path)
    plt.close()
    print(f"Saved: {fig6_path}")

    print("All 6 publication figures generated successfully.")

if __name__ == "__main__":
    generate_plots()

