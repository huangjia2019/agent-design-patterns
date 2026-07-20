# Full System Assembly

This directory keeps the historical `Argus Full Case` path while providing a
generic system-acceptance interface. It does not copy the perception, memory,
reasoning, action, reflection, collaboration, or governance implementations.
It verifies that their receipts belong to one run, workload, artifact lineage,
and business endpoint.

Core objects:

- `SystemRunContract`
- `ModuleReceipt`
- `EndpointEvidence`
- `audit_system()`
- `SystemAssembly`

Run:

```bash
cd composition/c-argus-full-case
python3 example.py
pytest -q

cd ../payroll-lab
python3 capstone_lab.py --mode bound
python3 capstone_lab.py --mode local-only
```

The digest chain demonstrates identity and lineage. It is not a digital
signature, external settlement receipt, durable event bus, or production IAM
system.
