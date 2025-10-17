#!/usr/bin/env python3
"""
Generate a machine-readable validation certificate that attests the project is
fully validated and aligned with the source paper for the specified season.

The certificate aggregates:
- Environment manifest (OS, Python, key package versions)
- Checksums of key inputs/outputs/artifacts
- Database sanity verification summary
- Paper case-study validation results across multiple seeds
- Training diagnostics (if available)

Output: validation_certificate.json (and optionally environment_manifest.json)
"""

import argparse
import hashlib
import json
import os
import platform
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime


# Ensure project imports work
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))


def safe_import(module: str):
    try:
        return __import__(module)
    except Exception:
        return None


def compute_sha256(file_path: Path) -> Optional[str]:
    try:
        if not file_path.exists() or not file_path.is_file():
            return None
        hasher = hashlib.sha256()
        with file_path.open('rb') as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception:
        return None


def gather_environment_manifest() -> Dict[str, Any]:
    manifest: Dict[str, Any] = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
        },
        "python": {
            "version": sys.version,
            "executable": sys.executable,
        },
        "packages": {}
    }

    def add_pkg(name: str):
        try:
            mod = __import__(name)
            ver = getattr(mod, "__version__", None)
            manifest["packages"][name] = ver if ver is not None else "unknown"
        except Exception:
            manifest["packages"][name] = None

    # Record commonly relevant packages; absent packages are recorded as None
    for pkg in [
        "numpy", "pandas", "sklearn", "cmdstanpy", "pystan", "arviz",
        "scipy", "joblib"
    ]:
        add_pkg(pkg)

    return manifest


def list_key_artifacts() -> List[Path]:
    return [
        PROJECT_ROOT / "src" / "nba_stats" / "db" / "nba_stats.db",
        PROJECT_ROOT / "production_bayesian_data.csv",
        PROJECT_ROOT / "stratified_sample_10k.csv",
        PROJECT_ROOT / "bayesian_model_k8.stan",
        PROJECT_ROOT / "trained_models" / "robust_scaler.joblib",
        PROJECT_ROOT / "trained_models" / "kmeans_model.joblib",
        PROJECT_ROOT / "lineup_supercluster_results" / "lineup_features_with_superclusters.csv",
        PROJECT_ROOT / "lineup_supercluster_results" / "supercluster_assignments.json",
        PROJECT_ROOT / "stan_model_results" / "convergence_diagnostics.json",
        PROJECT_ROOT / "stan_model_results" / "coefficient_summary.csv",
        PROJECT_ROOT / "stan_model_results" / "model_summary.csv",
    ]


def compute_artifact_checksums(paths: List[Path]) -> Dict[str, Optional[str]]:
    checksums: Dict[str, Optional[str]] = {}
    for p in paths:
        rel = str(p.relative_to(PROJECT_ROOT)) if p.exists() else str(p)
        checksums[rel] = compute_sha256(p)
    return checksums


def run_database_sanity() -> Dict[str, Any]:
    results: Dict[str, Any] = {
        "success": False,
        "summary": {},
        "details": []
    }
    try:
        from verify_database_sanity import DatabaseSanityVerifier
        verifier = DatabaseSanityVerifier(db_path=str(PROJECT_ROOT / "src" / "nba_stats" / "db" / "nba_stats.db"))
        success = verifier.run_verification()
        results["success"] = bool(success)
        # Aggregate a compact summary by layer
        layer_counts: Dict[str, Dict[str, int]] = {}
        for rec in getattr(verifier, "verification_results", []):
            layer = rec.get("layer", "unknown")
            status = rec.get("status", "unknown")
            if layer not in layer_counts:
                layer_counts[layer] = {"PASS": 0, "FAIL": 0, "WARN": 0}
            if status in layer_counts[layer]:
                layer_counts[layer][status] += 1
        results["summary"] = layer_counts
        results["critical_failures"] = getattr(verifier, "critical_failures", None)
    except Exception as e:
        results["error"] = f"database_sanity_exception: {e}"
    return results


def run_case_study_validation(season: str, cases: List[str], top_n: int, pass_threshold: int, seeds: List[int]) -> Dict[str, Any]:
    out: Dict[str, Any] = {
        "season": season,
        "top_n": top_n,
        "pass_threshold": pass_threshold,
        "seeds": seeds,
        "per_seed_results": [],
        "all_seeds_passed": False
    }
    try:
        # Import directly to avoid subprocess JSON parsing
        import validate_model as vm
        all_pass = True
        for seed in seeds:
            # set seeds via args; function does not accept seed, but evaluator uses numpy/random.
            # We set seeds here and rely on deterministic behavior of evaluator calls.
            import random as _rnd
            import numpy as _np
            _rnd.seed(seed)
            _np.random.seed(seed)
            res = vm.run_case_study_validation(
                season=season,
                cases=cases,
                top_n=top_n,
                pass_threshold=pass_threshold,
                debug=False
            )
            out["per_seed_results"].append({"seed": seed, "result": res})
            all_pass = all_pass and bool(res.get("all_passed", False))
        out["all_seeds_passed"] = all_pass
    except Exception as e:
        out["error"] = f"case_study_validation_exception: {e}"
    return out


def load_training_diagnostics() -> Dict[str, Any]:
    diag: Dict[str, Any] = {"available": False}
    try:
        diag_path = PROJECT_ROOT / "stan_model_results" / "convergence_diagnostics.json"
        if diag_path.exists():
            with diag_path.open('r') as f:
                data = json.load(f)
            diag.update({
                "available": True,
                "max_rhat": data.get("max_rhat"),
                "min_ess": data.get("min_ess"),
                "divergences": data.get("divergences"),
            })
            return diag
        # Fallback: try to infer from model_summary.csv
        summary_csv = PROJECT_ROOT / "stan_model_results" / "model_summary.csv"
        if summary_csv.exists():
            diag.update({"available": True, "summary_csv_present": True})
        return diag
    except Exception as e:
        diag["error"] = f"diagnostics_load_exception: {e}"
        return diag


def build_certificate(args: argparse.Namespace) -> Dict[str, Any]:
    env_manifest = gather_environment_manifest()
    checksums = compute_artifact_checksums(list_key_artifacts())
    db_sanity = run_database_sanity()
    case_results = run_case_study_validation(
        season=args.season,
        cases=args.cases or ["lakers", "pacers", "suns"],
        top_n=args.top_n,
        pass_threshold=args.pass_threshold,
        seeds=args.seeds or [42, 123, 456, 789, 999]
    )
    diagnostics = load_training_diagnostics()

    overall_pass = bool(db_sanity.get("success")) and bool(case_results.get("all_seeds_passed"))

    cert: Dict[str, Any] = {
        "certificate_version": 1,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "commit_hash": os.environ.get("GIT_COMMIT", None),
        "season": args.season,
        "environment": env_manifest,
        "artifacts": {
            "checksums_sha256": checksums
        },
        "database_sanity": db_sanity,
        "case_study_validation": case_results,
        "training_diagnostics": diagnostics,
        "recommended_validation_config": {
            "top_n": args.top_n,
            "pass_threshold": args.pass_threshold
        },
        "overall_pass": overall_pass
    }
    return cert


def write_json(path: Path, obj: Dict[str, Any]) -> None:
    with path.open('w') as f:
        json.dump(obj, f, indent=2, default=str)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate validation certificate")
    parser.add_argument("--season", default="2022-23", help="Season to validate against (default: 2022-23)")
    parser.add_argument("--cases", nargs="*", default=["lakers", "pacers", "suns"], help="Cases to validate")
    parser.add_argument("--top-n", type=int, default=5, dest="top_n", help="Top-N cutoff (default: 5)")
    parser.add_argument("--pass-threshold", type=int, default=3, dest="pass_threshold", help="Pass threshold (default: 3)")
    parser.add_argument("--seeds", nargs="*", type=int, default=[42, 123, 456, 789, 999], help="Seeds to test")
    parser.add_argument("--output", default="validation_certificate.json", help="Output path for certificate JSON")
    parser.add_argument("--emit-env-manifest", action="store_true", help="Also write environment_manifest.json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    certificate = build_certificate(args)

    # Write certificate
    out_path = PROJECT_ROOT / args.output
    write_json(out_path, certificate)
    print(f"\n📄 Validation certificate written to: {out_path}")
    print(f"   overall_pass = {certificate.get('overall_pass')}")

    # Optionally emit environment manifest separately
    if args.emit_env_manifest:
        env_path = PROJECT_ROOT / "environment_manifest.json"
        write_json(env_path, certificate.get("environment", {}))
        print(f"📄 Environment manifest written to: {env_path}")

    return 0 if certificate.get("overall_pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())



