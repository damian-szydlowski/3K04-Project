# Egram Data Model — Deliverable 1 (Part 2, item 5)

**Scope:** Front-end only (no serial). Define a minimal, clean structure to **capture** egram data now and reuse it later when communications are added.

**Code:** `DCM/models/egram_model.py`

---

## What we store

Each egram **sample** is a small dictionary:

```python
{
  "t_s": float,   # time in seconds (now)
  "raw": int,     # raw device units (lossless)
  "marker": str   # "--" (none), "VS" (ventricular sense), "VP" (ventricular pace), "()" (refractory)
}
```
