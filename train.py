"""Training harness for Path-Dependent Preferences.

Single-pass curriculum training: blocks are consumed strictly in curriculum
order, once. Macro phase boundaries (W / P / mixed / tail, from manifest.json)
are aligned to block boundaries -- no optimizer update mixes the end of one
phase with the start of the next. Flat LR after warmup. Word-level tokenizer.

Usage:
  python train.py --data data/smoke_L0 --curriculum pilot_p_only --seed 0 \\
      --outdir runs/pilot_p_only_L0_s0
  python train.py --data data/final_L0_seed0 --curriculum curriculum_C1 \\
      --seed 0 --outdir runs/C1_L0_s0
"""

import argparse
import datetime
import hashlib
import json
import math
import platform
import random
import subprocess
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

PAD, EOL = "<pad>", "<eol>"


# --- tokenizer ---------------------------------------------------------------

def build_vocab(data_dir):
    """Word-level vocab over every text/jsonl file in the data dir (stable order)."""
    words = set()
    for f in sorted(Path(data_dir).glob("*.txt")):
        words.update(f.read_text().split())
    for f in sorted(Path(data_dir).glob("*.jsonl")):
        for line in f.read_text().splitlines():
            r = json.loads(line)
            words.update(r["prompt"].split())
            if "line" in r:
                words.update(r["line"].split())
    words.update(["A:", "Option", "1", "2"])
    vocab = [PAD, EOL] + sorted(words)
    return {w: i for i, w in enumerate(vocab)}


def encode(text, stoi):
    return [stoi[w] for w in text.split()]


# --- data packing ------------------------------------------------------------

def pack_segments(lines, segments, stoi, block):
    """Token blocks per macro segment; each segment starts on a fresh block.

    Returns (blocks int32 array [n, block], loss_mask bool array, seg_ranges).
    """
    all_blocks, seg_ranges, i = [], [], 0
    for seg_name, n_lines in segments:
        stream = []
        for line in lines[i:i + n_lines]:
            stream.extend(encode(line, stoi))
            stream.append(stoi[EOL])
        i += n_lines
        start = len(all_blocks)
        for j in range(0, len(stream), block):
            chunk = stream[j:j + block]
            chunk += [stoi[PAD]] * (block - len(chunk))
            all_blocks.append(chunk)
        seg_ranges.append({"segment": seg_name, "block_start": start,
                           "block_end": len(all_blocks)})
    arr = np.array(all_blocks, dtype=np.int64)
    mask = arr != stoi[PAD]
    return arr, mask, seg_ranges


# --- model -------------------------------------------------------------------

class Block(nn.Module):
    def __init__(self, d, heads):
        super().__init__()
        self.ln1, self.ln2 = nn.LayerNorm(d), nn.LayerNorm(d)
        self.qkv = nn.Linear(d, 3 * d)
        self.proj = nn.Linear(d, d)
        self.mlp = nn.Sequential(nn.Linear(d, 4 * d), nn.GELU(),
                                 nn.Linear(4 * d, d))
        self.heads = heads

    def forward(self, x):
        B, T, D = x.shape
        q, k, v = self.qkv(self.ln1(x)).split(D, dim=2)
        shape = (B, T, self.heads, D // self.heads)
        q, k, v = (t.view(shape).transpose(1, 2) for t in (q, k, v))
        a = F.scaled_dot_product_attention(q, k, v, is_causal=True)
        x = x + self.proj(a.transpose(1, 2).reshape(B, T, D))
        return x + self.mlp(self.ln2(x))


class GPT(nn.Module):
    def __init__(self, vocab_size, d=384, layers=6, heads=6, block=320):
        super().__init__()
        self.tok = nn.Embedding(vocab_size, d)
        self.pos = nn.Embedding(block, d)
        self.blocks = nn.ModuleList(Block(d, heads) for _ in range(layers))
        self.ln_f = nn.LayerNorm(d)
        self.head = nn.Linear(d, vocab_size, bias=False)
        self.block_size = block

    def forward(self, idx, return_hidden=False):
        T = idx.shape[1]
        x = self.tok(idx) + self.pos(torch.arange(T, device=idx.device))
        hiddens = []
        for b in self.blocks:
            x = b(x)
            if return_hidden:
                hiddens.append(x)
        x = self.ln_f(x)
        logits = self.head(x)
        return (logits, hiddens) if return_hidden else logits


# --- reproducibility ---------------------------------------------------------

def seed_everything(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def sha256_state(model):
    h = hashlib.sha256()
    for k, v in sorted(model.state_dict().items()):
        h.update(k.encode())
        h.update(v.detach().cpu().numpy().tobytes())
    return h.hexdigest()


def git_commit():
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True,
                              text=True).stdout.strip()
    except Exception:
        return "unknown"


def pick_device(arg):
    if arg != "auto":
        return arg
    if torch.cuda.is_available():
        return "cuda"
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


# --- training ----------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--curriculum", required=True,
                    help="basename without .txt, e.g. curriculum_C1 or pilot_p_only")
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--d_model", type=int, default=384)
    ap.add_argument("--layers", type=int, default=6)
    ap.add_argument("--heads", type=int, default=6)
    ap.add_argument("--block", type=int, default=320)
    ap.add_argument("--batch", type=int, default=64)
    ap.add_argument("--lr", type=float, default=3e-4)
    ap.add_argument("--warmup", type=int, default=200)
    ap.add_argument("--wd", type=float, default=0.1)
    ap.add_argument("--clip", type=float, default=1.0)
    ap.add_argument("--ckpt_every_pct", type=float, default=5.0)
    ap.add_argument("--epochs", type=int, default=1,
                    help="repeat the identical block sequence N times. "
                         "Diagnostic/pilot use; the main experiment is "
                         "single-pass per the prereg epoch rule")
    ap.add_argument("--device", default="auto")
    args = ap.parse_args()

    data_dir, outdir = Path(args.data), Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    device = pick_device(args.device)
    seed_everything(args.seed)

    stoi = build_vocab(data_dir)
    (outdir / "vocab.json").write_text(json.dumps(stoi))
    manifest = json.loads((data_dir / "manifest.json").read_text())
    cur_file = data_dir / f"{args.curriculum}.txt"
    lines = cur_file.read_text().splitlines()
    cond = args.curriculum.replace("curriculum_", "")
    segments = manifest["segments"].get(cond, [("mixed", len(lines))])

    blocks, mask, seg_ranges = pack_segments(lines, segments, stoi, args.block)
    if args.epochs > 1:
        blocks = np.concatenate([blocks] * args.epochs)
        mask = np.concatenate([mask] * args.epochs)
    n_steps = math.ceil(len(blocks) / args.batch)
    warmup = min(args.warmup, max(1, n_steps // 10))

    model = GPT(len(stoi), args.d_model, args.layers, args.heads,
                args.block).to(device)
    init_hash = sha256_state(model)
    n_params = sum(p.numel() for p in model.parameters())
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr,
                            weight_decay=args.wd)

    commit = git_commit()
    run_manifest = {
        "run_id": f"{args.curriculum}-s{args.seed}-{commit[:8]}-{n_steps}st",
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "calibration_version": 3,
        "git_commit": commit, "dataset_dir": str(data_dir),
        "curriculum": args.curriculum,
        "curriculum_sha256": sha256_file(cur_file),
        "vocab_sha256": hashlib.sha256(
            json.dumps(stoi).encode()).hexdigest(),
        "initialization_sha256": init_hash, "seed": args.seed,
        "n_lines": len(lines), "n_blocks": int(len(blocks)),
        "n_steps": n_steps, "warmup": warmup, "segments": seg_ranges,
        "config": vars(args), "n_params": n_params,
        "torch": torch.__version__, "device": device,
        "platform": platform.platform(),
    }
    (outdir / "run_manifest.json").write_text(json.dumps(run_manifest, indent=2))

    torch.save(model.state_dict(), outdir / "ckpt_000.pt")   # init checkpoint
    ckpt_steps = {max(1, round(n_steps * p / 100)): int(p)
                  for p in np.arange(args.ckpt_every_pct, 100.01,
                                     args.ckpt_every_pct)}
    # Preserve FULL training state (Adam moments + RNG) at every segment
    # boundary and at the end — the developmental history lives in
    # (theta, m, v), and Phase B's crossed weight x optimizer-state
    # transplant needs these states without retraining. ~90MB each.
    boundary_steps = sorted({min(n_steps, math.ceil(r["block_end"] / args.batch))
                             for r in seg_ranges} | {n_steps})

    def save_train_state(step1):
        torch.save({
            "step": step1, "optimizer": opt.state_dict(),
            "torch_rng": torch.get_rng_state(),
            "cuda_rng": (torch.cuda.get_rng_state_all()
                         if torch.cuda.is_available() else None),
            "np_rng": np.random.get_state(), "py_rng": random.getstate(),
        }, outdir / f"trainstate_{step1:06d}.pt")

    log = []
    model.train()
    for step in range(n_steps):
        lo, hi = step * args.batch, min((step + 1) * args.batch, len(blocks))
        xb = torch.from_numpy(blocks[lo:hi]).to(device)
        mb = torch.from_numpy(mask[lo:hi]).to(device)
        logits = model(xb)
        tgt = xb[:, 1:].clone()
        tgt[~mb[:, 1:]] = -100
        loss = F.cross_entropy(logits[:, :-1].reshape(-1, logits.shape[-1]),
                               tgt.reshape(-1), ignore_index=-100)
        lr = args.lr * min(1.0, (step + 1) / warmup)
        for g in opt.param_groups:
            g["lr"] = lr
        opt.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), args.clip)
        opt.step()
        if step % 20 == 0 or step == n_steps - 1:
            log.append({"step": step, "loss": float(loss.item()), "lr": lr})
            print(f"step {step + 1}/{n_steps} loss {loss.item():.4f}")
        if (step + 1) in ckpt_steps:
            pct = ckpt_steps[step + 1]
            torch.save(model.state_dict(), outdir / f"ckpt_{pct:03d}.pt")
        if (step + 1) in boundary_steps:
            save_train_state(step + 1)
    (outdir / "train_log.json").write_text(json.dumps(log))
    print(f"done: {n_steps} steps, {n_params/1e6:.1f}M params, "
          f"init {init_hash[:12]}")


if __name__ == "__main__":
    main()
