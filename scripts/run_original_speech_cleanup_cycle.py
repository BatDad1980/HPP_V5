"""Run a bounded speech-cleanup training cycle in the original HPP branch.

This trains only speech-facing layers, saves a separate cleanup checkpoint, and
does not overwrite the current original `hpp_linguistic_anchor.pth` unless
explicitly requested.
"""

from __future__ import annotations

import argparse
import gc
import json
import math
import os
import random
import sys
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

import torch
import torch.nn as nn
import torch.optim as optim


DEFAULT_ORIGINAL = Path(
    r"C:\Users\Aural\Desktop\Codename HYPERPLASTICITY PROTOCOL\Project_HPP"
)


@contextmanager
def pushd(path: Path) -> Iterator[None]:
    previous = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(previous)


def cuda_report(device: torch.device) -> dict[str, object]:
    if device.type != "cuda":
        return {
            "device": str(device),
            "allocated_mb": 0.0,
            "reserved_mb": 0.0,
            "max_allocated_mb": 0.0,
        }
    return {
        "device": str(device),
        "name": torch.cuda.get_device_name(device),
        "allocated_mb": round(torch.cuda.memory_allocated(device) / 1024 / 1024, 2),
        "reserved_mb": round(torch.cuda.memory_reserved(device) / 1024 / 1024, 2),
        "max_allocated_mb": round(torch.cuda.max_memory_allocated(device) / 1024 / 1024, 2),
    }


def save_checkpoint(engine: object, path: Path, step: int, loss: float, phase: str) -> None:
    payload = {
        "masamune_state_dict": engine.university.state_dict(),
        "lm_head_state_dict": engine.lm_head.state_dict(),
        "embedding_state_dict": engine.embedding.state_dict(),
        "step": step,
        "loss": loss,
        "phase": phase,
    }
    torch.save(payload, path)
    print(f"[SAVE] {path} step={step} loss={loss:.4f}", flush=True)


def load_data(path: Path) -> list[dict[str, str]]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def build_training_example(engine: object, sample: dict[str, str], seq_len: int) -> tuple[list[int], list[int]]:
    """Return token ids and labels with prompt tokens masked out."""
    instruction = str(sample.get("instruction", "")).strip()
    response = str(sample.get("response", "")).strip()

    prompt_text = f"User: {instruction}\nAssistant:"
    response_text = f" {response}"
    prompt_tokens = engine.enc.encode(prompt_text)
    response_tokens = engine.enc.encode(response_text)
    tokens = (prompt_tokens + response_tokens)[:seq_len]

    labels = tokens.copy()
    prompt_cutoff = min(len(prompt_tokens), len(labels))
    for index in range(prompt_cutoff):
        labels[index] = -100

    if len(tokens) < seq_len:
        pad = seq_len - len(tokens)
        tokens += [engine.enc.eot_token] * pad
        labels += [-100] * pad

    return tokens, labels


def set_trainable(
    engine: object,
    *,
    train_embedding: bool,
    train_compass: bool,
    train_all_domains: bool,
) -> list[torch.nn.Parameter]:
    for parameter in engine.university.parameters():
        parameter.requires_grad = False
    for parameter in engine.embedding.parameters():
        parameter.requires_grad = False
    for parameter in engine.lm_head.parameters():
        parameter.requires_grad = False

    for module in [
        engine.hpp_core,
        engine.guardian,
        engine.toddler,
        engine.school,
        engine.adolescent,
    ]:
        for parameter in module.parameters():
            parameter.requires_grad = False

    trainable = []

    modules = [engine.lm_head, engine.university.output_norm, engine.university.swarm_gate]

    if train_embedding:
        modules.append(engine.embedding)

    if train_compass:
        modules.append(engine.university.compass)

    if train_all_domains:
        modules.extend(engine.university.domain_expertise.values())
    else:
        modules.append(engine.university.domain_expertise["conversation"])

    for module in modules:
        for parameter in module.parameters():
            parameter.requires_grad = True
            trainable.append(parameter)
    return trainable


def get_lr(step: int, steps: int, lr: float, warmup: int) -> float:
    if step < warmup:
        return lr * max(step, 1) / max(warmup, 1)
    progress = (step - warmup) / max(steps - warmup, 1)
    return lr * 0.5 * (1.0 + math.cos(math.pi * progress))


def run(args: argparse.Namespace) -> dict[str, object]:
    sys.path.insert(0, str(args.original))
    dataset_path = args.original / "datasets" / "hf_local" / args.dataset
    checkpoint_path = args.original / "checkpoints" / args.output_checkpoint

    with pushd(args.original):
        from hpp_sovereign_engine import HPP_SovereignEngine

        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        if device.type == "cuda":
            torch.cuda.empty_cache()
            torch.cuda.reset_peak_memory_stats(device)

        print(f"[INIT] device={device}", flush=True)
        engine = HPP_SovereignEngine(max_context=512)
        trainable = set_trainable(
            engine,
            train_embedding=args.train_embedding,
            train_compass=args.train_compass,
            train_all_domains=args.train_all_domains,
        )
        data = load_data(dataset_path)
        print(f"[DATA] {len(data)} rows from {dataset_path}", flush=True)
        print(f"[TRAINABLE] {sum(p.numel() for p in trainable):,} params", flush=True)

        optimizer = optim.AdamW(trainable, lr=args.lr, weight_decay=args.weight_decay)
        criterion = nn.CrossEntropyLoss(ignore_index=-100)

        engine.university.train()
        engine.lm_head.train()
        engine.embedding.train()

        memory_start = cuda_report(device)
        t0 = time.time()
        loss_val = float("nan")

        for step in range(1, args.steps + 1):
            current_lr = get_lr(step, args.steps, args.lr, args.warmup)
            for group in optimizer.param_groups:
                group["lr"] = current_lr

            batch = random.choices(data, k=args.batch)
            token_batch = []
            label_batch = []
            for sample in batch:
                tokens, labels = build_training_example(engine, sample, args.seq_len)
                token_batch.append(tokens)
                label_batch.append(labels)

            ids = torch.tensor(token_batch, dtype=torch.long, device=device)
            labels = torch.tensor(label_batch, dtype=torch.long, device=device)
            optimizer.zero_grad(set_to_none=True)
            embedded = engine.embedding(ids[:, :-1]).permute(1, 0, 2)
            output = engine.university(embedded, domain="conversation")
            logits = engine.lm_head(output).permute(1, 2, 0)
            loss = criterion(logits, labels[:, 1:])
            loss.backward()
            torch.nn.utils.clip_grad_norm_(trainable, max_norm=1.0)
            optimizer.step()

            loss_val = float(loss.item())
            if step == 1 or step % args.log_every == 0:
                elapsed = time.time() - t0
                print(
                    f"[STEP] {step:5d}/{args.steps} loss={loss_val:.4f} "
                    f"lr={current_lr:.2e} elapsed={elapsed:.0f}s",
                    flush=True,
                )

            del loss, logits, output, embedded, ids, labels
            if step % args.gc_every == 0:
                gc.collect()
                if device.type == "cuda":
                    torch.cuda.empty_cache()

            if args.save_every and step % args.save_every == 0:
                save_checkpoint(engine, checkpoint_path, step, loss_val, args.phase)

        save_checkpoint(engine, checkpoint_path, args.steps, loss_val, args.phase)
        memory_end = cuda_report(device)

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "original": str(args.original),
        "dataset": str(dataset_path),
        "output_checkpoint": str(checkpoint_path),
        "steps": args.steps,
        "batch": args.batch,
        "seq_len": args.seq_len,
        "lr": args.lr,
        "warmup": args.warmup,
        "train_embedding": args.train_embedding,
        "train_compass": args.train_compass,
        "train_all_domains": args.train_all_domains,
        "final_loss": loss_val,
        "memory_start": memory_start,
        "memory_end": memory_end,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--original", type=Path, default=DEFAULT_ORIGINAL)
    parser.add_argument("--dataset", type=str, default="CONVERSATIONAL_CLEANUP_V1.jsonl")
    parser.add_argument("--output-checkpoint", type=str, default="hpp_speech_cleanup_v1.pth")
    parser.add_argument("--phase", type=str, default="speech_cleanup_v1")
    parser.add_argument("--steps", type=int, default=2500)
    parser.add_argument("--batch", type=int, default=2)
    parser.add_argument("--seq-len", type=int, default=96)
    parser.add_argument("--lr", type=float, default=8e-5)
    parser.add_argument("--warmup", type=int, default=250)
    parser.add_argument("--weight-decay", type=float, default=0.01)
    parser.add_argument("--train-embedding", action="store_true")
    parser.add_argument("--train-compass", action="store_true")
    parser.add_argument("--train-all-domains", action="store_true")
    parser.add_argument("--log-every", type=int, default=100)
    parser.add_argument("--gc-every", type=int, default=50)
    parser.add_argument("--save-every", type=int, default=500)
    parser.add_argument("--report", type=Path, default=Path("docs/original-speech-cleanup-cycle.json"))
    args = parser.parse_args()

    report = run(args)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
