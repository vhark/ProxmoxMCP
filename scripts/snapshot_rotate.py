#!/usr/bin/env python3

import argparse
import json
import sys
from datetime import datetime, timedelta
from proxmoxer import ProxmoxAPI


def load_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def connect_proxmox(config: dict) -> ProxmoxAPI:
    prox = config["proxmox"]
    auth = config["auth"]
    return ProxmoxAPI(
        prox["host"],
        user=auth["user"],
        token_name=auth["token_name"],
        token_value=auth["token_value"],
        verify_ssl=prox.get("verify_ssl", True),
        port=prox.get("port", 8006),
    )


def tag_snapshot_name(prefix: str) -> str:
    now = datetime.utcnow()
    if prefix == "hourly":
        return f"auto-hourly-{now:%Y%m%d-%H%M}"
    if prefix == "daily":
        return f"auto-daily-{now:%Y%m%d}"
    if prefix == "weekly":
        return f"auto-weekly-{now:%Y%m%d}"
    if prefix == "monthly":
        return f"auto-monthly-{now:%Y%m%d}"
    raise ValueError(f"Unknown prefix {prefix}")


def parse_snapshot_timestamp(name: str) -> datetime | None:
    try:
        if not name.startswith("auto-"):
            return None
        parts = name.split("-")
        if len(parts) < 3:
            return None
        cadence = parts[1]
        stamp = "-".join(parts[2:])
        if cadence == "hourly":
            return datetime.strptime(stamp, "%Y%m%d-%H%M")
        return datetime.strptime(stamp, "%Y%m%d")
    except Exception:
        return None


def should_create(now: datetime) -> list[str]:
    cadences = ["hourly"]
    if now.minute == 0:
        cadences.append("daily")
    if now.weekday() == 0 and now.hour == 0 and now.minute == 0:
        cadences.append("weekly")
    if now.day == 1 and now.hour == 0 and now.minute == 0:
        cadences.append("monthly")
    return cadences


def retention_cutoffs(now: datetime) -> dict:
    return {
        "hourly": now - timedelta(days=3),
        "daily": now - timedelta(days=14),
        "weekly": now - timedelta(weeks=8),
        "monthly": now - timedelta(days=730),
    }


def filter_snapshots(snapshots: list[dict]) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = {"hourly": [], "daily": [], "weekly": [], "monthly": []}
    for snap in snapshots:
        name = snap.get("name", "")
        if not name.startswith("auto-"):
            continue
        parts = name.split("-")
        if len(parts) < 3:
            continue
        cadence = parts[1]
        if cadence in grouped:
            grouped[cadence].append(snap)
    return grouped


def prune_snapshots(proxmox: ProxmoxAPI, node: str, vmid: str, snapshots: list[dict], cutoff: datetime, dry_run: bool) -> None:
    for snap in snapshots:
        name = snap.get("name", "")
        ts = parse_snapshot_timestamp(name)
        if not ts:
            continue
        if ts < cutoff:
            if dry_run:
                print(f"[dry-run] delete {vmid}@{name}")
            else:
                proxmox.nodes(node).qemu(vmid).snapshot(name).delete()
                print(f"Deleted {vmid}@{name}")


def create_snapshot(proxmox: ProxmoxAPI, node: str, vmid: str, cadence: str, dry_run: bool) -> None:
    name = tag_snapshot_name(cadence)
    if dry_run:
        print(f"[dry-run] create {vmid}@{name}")
        return
    proxmox.nodes(node).qemu(vmid).snapshot.post(snapname=name)
    print(f"Created {vmid}@{name}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Proxmox snapshot rotation")
    parser.add_argument("--config", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    config = load_config(args.config)
    proxmox = connect_proxmox(config)

    now = datetime.utcnow()
    cadences_to_create = should_create(now)
    cutoffs = retention_cutoffs(now)

    vms = proxmox.cluster.resources.get(type="vm")
    for vm in vms:
        if vm.get("template"):
            continue
        vmid = str(vm.get("vmid"))
        node = vm.get("node")
        if not node:
            continue

        try:
            snapshots = proxmox.nodes(node).qemu(vmid).snapshot.get()
        except Exception as exc:
            print(f"[warn] skipping vmid {vmid} on {node}: {exc}")
            continue

        grouped = filter_snapshots(snapshots)

        for cadence in cadences_to_create:
            create_snapshot(proxmox, node, vmid, cadence, args.dry_run)

        for cadence, snaps in grouped.items():
            prune_snapshots(proxmox, node, vmid, snaps, cutoffs[cadence], args.dry_run)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
