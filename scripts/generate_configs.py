"""
Generate FIO job configuration files for CS559 System Design Storage Performance Lab.
Workloads:
  Case A: Random read, 4 KiB, 100% Read, QD in [1, 8, 32]
  Case B: Random mixed R/W, 4 KiB, 70% Read / 30% Write, QD in [1, 8, 32]
  Case C: Random mixed R/W, 8 KiB, 30% Read / 70% Write, QD in [1, 8, 32]
  Case D: Sequential read, 256 KiB, 100% Read, QD in [1, 8, 32]
"""
import os

CONFIGS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "configs")
os.makedirs(CONFIGS_DIR, exist_ok=True)

EXPERIMENTS = [
    {
        "case": "Case_A",
        "name": "Point_Lookups_Index_Access",
        "rw": "randread",
        "bs": "4k",
        "rwmixread": 100,
        "description": "PostgreSQL B-Tree index lookup / single row point queries"
    },
    {
        "case": "Case_B",
        "name": "Read_Heavy_OLTP_Transactional",
        "rw": "randrw",
        "bs": "4k",
        "rwmixread": 70,
        "description": "PostgreSQL OLTP read-heavy transaction mix (70% read / 30% write)"
    },
    {
        "case": "Case_C",
        "name": "Write_Heavy_Checkpoint_Batch",
        "rw": "randrw",
        "bs": "8k",
        "rwmixread": 30,
        "description": "PostgreSQL write-heavy checkpointer page flush / batch update (30% read / 70% write, 8KB native page)"
    },
    {
        "case": "Case_D",
        "name": "Sequential_Table_Scan_Analytics",
        "rw": "read",
        "bs": "256k",
        "rwmixread": 100,
        "description": "PostgreSQL sequential scan, analytical aggregation, VACUUM, pg_dump"
    }
]

QUEUE_DEPTHS = [1, 8, 32]

def generate_fio_job(exp, qd):
    content = f"""; CS559 System Design - FIO Benchmark Configuration
; Workload: {exp['case']} ({exp['name']})
; Queue Depth: {qd}
; Purpose: {exp['description']}

[global]
ioengine=libaio
direct=1
size=1g
runtime=20
time_based=1
ramp_time=3
group_reporting=1
filename=/root/fio-lab/db-test.bin
percentile_list=50:95:99

[{exp['case']}_qd{qd}]
rw={exp['rw']}
bs={exp['bs']}
"""
    if exp['rw'] == 'randrw':
        content += f"rwmixread={exp['rwmixread']}\n"
    content += f"iodepth={qd}\nnumjobs=1\n"
    return content

# Master template file
master_template = """; CS559 System Design - Master FIO Template
; Flexible I/O Tester (FIO) Global Template for Storage Performance Benchmarking

[global]
ioengine=libaio
direct=1
size=1g
runtime=20
time_based=1
ramp_time=3
group_reporting=1
filename=/root/fio-lab/db-test.bin
percentile_list=50:95:99
numjobs=1

; Example job definition:
; [example-job]
; rw=randread
; bs=4k
; iodepth=8
"""

with open(os.path.join(CONFIGS_DIR, "template.fio"), "w") as f:
    f.write(master_template)

for exp in EXPERIMENTS:
    # Also generate a consolidated case file containing all 3 queue depths for ease of inspection
    consolidated = f"""; CS559 System Design - {exp['case']} Full Suite
; Workload: {exp['name']}
; Access pattern: rw={exp['rw']}, bs={exp['bs']}, rwmixread={exp['rwmixread']}%

[global]
ioengine=libaio
direct=1
size=1g
runtime=20
time_based=1
ramp_time=3
group_reporting=1
filename=/root/fio-lab/db-test.bin
percentile_list=50:95:99
numjobs=1

"""
    for qd in QUEUE_DEPTHS:
        filename = f"{exp['case'].lower()}_qd{qd}.fio"
        filepath = os.path.join(CONFIGS_DIR, filename)
        job_content = generate_fio_job(exp, qd)
        with open(filepath, "w") as f:
            f.write(job_content)
        print(f"Generated: {filepath}")

        consolidated += f"[{exp['case']}_qd{qd}]\nrw={exp['rw']}\nbs={exp['bs']}\n"
        if exp['rw'] == 'randrw':
            consolidated += f"rwmixread={exp['rwmixread']}\n"
        consolidated += f"iodepth={qd}\n\n"

    cons_path = os.path.join(CONFIGS_DIR, f"{exp['case'].lower()}_all.fio")
    with open(cons_path, "w") as f:
        f.write(consolidated)
    print(f"Generated: {cons_path}")

print("All FIO job files generated successfully.")

