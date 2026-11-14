# CS559 System Design: Measuring Storage Performance with FIO
### From Database Access Patterns to Reproducible I/O Experiments

**Author:** Abhigyan Sharma  
**Course:** CS559 System Design  
**Target Database Archetype:** PostgreSQL 16 (Relational OLTP / Mixed Analytics)  
**Deliverables:** Research Report (PDF), FIO Job Files (`.fio`), Raw JSON Outputs, Processed CSVs, Publication Figures, Python Automation Suite.

---

## 1. Executive Summary & Chosen Database

### Selected Database: PostgreSQL 16
* **Database Name & Version:** PostgreSQL 16.3 (64-bit on Linux / WSL2)
* **Justification:** PostgreSQL is the industry-standard open-source relational database underpinning modern transactional and analytical platforms. Its storage subsystem is transparent, well-documented, and directly models the four experimental I/O patterns evaluated in this study.
* **Architecture & Storage Model:**
  * **Page Buffer Size:** PostgreSQL operates with an **8 KiB default disk block size** in shared buffers (`shared_buffers`).
  * **Index Operations:** B-Tree index leaf traversals and primary key point lookups perform scattered 4 KiB to 8 KiB random reads.
  * **OLTP Transactions:** Read-heavy transactional workloads (e.g., TPC-C) mix random reads with tuple inserts, updates, and MVCC visibility checks.
  * **Checkpointing & Dirty Page Flushes:** The background checkpointer flushes dirty 8 KiB shared buffer pages to disk under heavy write load.
  * **Sequential Heap Scans:** Analytical queries (`SELECT COUNT(*)`, aggregations, `VACUUM`, and `pg_dump`) stream contiguous blocks using aggressive OS/PostgreSQL read-ahead (128 KiB to 256 KiB chunks).
* **Important Limitations (Synthetic FIO vs. Real Database):**
  FIO generates synthetic block-level storage I/O. It **does not** execute SQL queries, maintain an Abstract Syntax Tree (AST), manage lock tables, perform MVCC page garbage collection, or leverage multi-tier DRAM caching. Real databases achieve 90%+ hit ratios in `shared_buffers`; FIO with `direct=1` bypasses the OS page cache to benchmark raw physical and virtualized block-layer performance.

---

## 2. Experimental Workload Mapping

| Case | Pattern (`rw`) | Block Size (`bs`) | Read Mix (`rwmixread`) | Queue Depth (`iodepth`) | PostgreSQL Workload Analogue |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Case A** | `randread` | 4 KiB | 100% | 1, 8, 32 | **B-Tree Index Lookups & Point Queries:** `SELECT * FROM tbl WHERE id = ?` missing shared buffers. |
| **Case B** | `randrw` | 4 KiB | 70% Read / 30% Write | 1, 8, 32 | **Read-Heavy OLTP Transactions:** Standard customer transactions updating balances and reading catalogue rows. |
| **Case C** | `randrw` | 8 KiB | 30% Read / 70% Write | 1, 8, 32 | **Write-Heavy Checkpointing:** Checkpointer flushing dirty 8 KiB pages during intensive ingestion/batch updates. |
| **Case D** | `read` (seq) | 256 KiB | 100% | 1, 8, 32 | **Analytical Table Scans & Utilities:** Full sequential scans, bulk analytical queries, `VACUUM`, and `pg_dump`. |

---

## 3. Testbed & System Environment

All benchmarks were executed on an isolated, pre-allocated file target under strictly controlled conditions:

| Parameter | Value / Specification |
| :--- | :--- |
| **Host Processor** | 13th Gen Intel(R) Core(TM) i7-13620H (16 vCPUs, up to 4.9 GHz) |
| **Host Operating System** | Windows 11 Home (Build 10.0.26100) |
| **Guest OS / Subsystem** | Ubuntu 24.04 LTS via Windows Subsystem for Linux (WSL2) |
| **Linux Kernel** | `6.6.87.2-microsoft-standard-WSL2` (x86_64) |
| **FIO Version** | `fio-3.41` (installed via Ubuntu package manager) |
| **I/O Engine** | `libaio` (Linux Native Asynchronous I/O) |
| **Caching Mode** | `direct=1` (`O_DIRECT`, strict page cache bypass) |
| **Working Target** | `/root/fio-lab/db-test.bin` (Pre-allocated 1.0 GiB file on native ext4) |
| **Runtime & Warm-up** | `runtime=20s`, `ramp_time=3s`, `time_based=1` |
| **Statistical Rigor** | 3 independent repetitions per condition (36 benchmark runs total) |

> **WSL2 Ext4 Note:** Running FIO against `/mnt/c` introduces severe 9p/Plan9 network translation bottlenecks. All benchmarks in this study strictly targeted the native virtualized ext4 filesystem at `/root/fio-lab/db-test.bin`, avoiding host filesystem translation penalties while capturing realistic virtualized block device performance.

---

## 4. Repository Structure

```text
FIO/
├── CS559_Storage_Performance_Report.pdf  # Comprehensive 5-6 Page Academic Report
├── README.md                             # Reproducibility manual & technical specifications
├── configs/                              # 12 Individual + 4 consolidated .fio job files
│   ├── template.fio                      # Global template
│   ├── case_a_qd1.fio, case_a_qd8.fio, case_a_qd32.fio, case_a_all.fio
│   ├── case_b_qd1.fio, case_b_qd8.fio, case_b_qd32.fio, case_b_all.fio
│   ├── case_c_qd1.fio, case_c_qd8.fio, case_c_qd32.fio, case_c_all.fio
│   └── case_d_qd1.fio, case_d_qd8.fio, case_d_qd32.fio, case_d_all.fio
├── raw_results/                          # 36 Raw FIO JSON execution results
│   ├── case_a_qd1_rep1.json ... case_d_qd32_rep3.json
├── processed_data/                       # Parsed statistical datasets
│   ├── benchmark_raw_metrics.csv         # All 36 raw data points
│   └── benchmark_summary.csv             # Mean ± SD, P50, P95, P99 across repetitions
├── figures/                              # 300 DPI publication plots
│   ├── fig1_iops_scaling.png             # IOPS vs Queue Depth
│   ├── fig2_bandwidth_scaling.png        # Bandwidth (MiB/s) vs Queue Depth
│   ├── fig3_average_latency.png          # Average Latency inflation
│   ├── fig4_tail_latency_p99.png         # P50, P95, P99 Percentiles at QD=32
│   ├── fig5_tradeoff_iops_latency.png    # Throughput vs Latency (The Saturation Knee)
│   └── fig6_read_write_mix_comparison.png# Case B vs Case C comparison
└── scripts/                              # Automated benchmarking & reporting pipeline
    ├── generate_configs.py               # Generates all .fio job files
    ├── run_benchmarks.py                 # Runs 36 tests and parses JSON
    ├── parse_and_plot.py                 # Generates publication figures
    └── generate_report_pdf.py            # Compiles the final PDF report
```

---

## 5. Step-by-Step Reproduction Instructions

### Step 1: Install WSL2 and Ubuntu
In PowerShell (Administrator):
```powershell
wsl --install Ubuntu --no-launch
```

### Step 2: Install FIO in WSL2
Inside Ubuntu WSL:
```bash
wsl -d Ubuntu -u root
apt-get update && apt-get install -y fio python3 python3-pip
```

### Step 3: Pre-allocate the Benchmark Target File
```bash
mkdir -p /root/fio-lab
dd if=/dev/zero of=/root/fio-lab/db-test.bin bs=1M count=1024 status=progress
```

### Step 4: Run the Full Benchmark Suite
From the repository root in PowerShell:
```powershell
python scripts\run_benchmarks.py
```
This executes all 36 runs (12 conditions × 3 repetitions), logs real-time metrics to stdout, writes raw JSONs into `raw_results/`, and saves parsed datasets into `processed_data/`.

### Step 5: Generate Figures and Final PDF Report
```powershell
python scripts\parse_and_plot.py
python scripts\generate_report_pdf.py
```

To run a single job file manually via FIO:
```bash
wsl -d Ubuntu -u root -- fio /mnt/c/Users/Abhigyan\ Sharma/OneDrive/Desktop/FIO/configs/case_a_qd8.fio --output=output.json --output-format=json
```

---

## 6. Key Empirical Findings & Summary

1. **Random vs. Sequential Disparity:** At QD=32, Case A (4 KiB random read) achieves ~34,000 IOPS but only ~133 MiB/s, while Case D (256 KiB sequential read) reaches ~1,300 MiB/s at ~5,200 IOPS. Sequential streaming achieves a ~10x bandwidth advantage by exploiting multi-channel flash parallelism and DMA transfers.
2. **Diminishing Returns & The Saturation Knee:** Moving from QD=1 to QD=8 doubles IOPS across all workloads with negligible latency impact. However, increasing from QD=8 to QD=32 increases IOPS by only ~8% while latency inflates by 3.85x. Systems architects should cap concurrency at QD=8 to QD=16.
3. **Write Penalty on Flash:** High write intensity (Case C, 70% write) reduces IOPS by ~35% and introduces severe P99 tail latency spikes (~3.85 ms) due to flash block erase cycles, garbage collection, and flush barriers.
4. **Tail Latency vs. Average:** Average latency conceals severe outlier delays. While average latency at QD=32 was ~900 μs, P99 tail latency reached nearly 4,000 μs. Interactive database systems must be sized based on P99 SLA limits, not averages.

