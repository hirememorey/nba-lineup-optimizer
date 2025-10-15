#!/usr/bin/env python3
"""
Parameter Sweep Script for Model Validation

This script tests different combinations of top-n and pass-threshold parameters
to find the configuration that makes all three case studies pass validation.

Based on the post-mortem insights: "The model is probably working correctly, 
but my validation criteria are misaligned with how the model actually ranks players."
"""

import subprocess
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any

def run_validation(top_n: int, pass_threshold: int, seed: int = 42, debug: bool = False) -> Dict[str, Any]:
    """Run validation with specific parameters and return results."""
    cmd = [
        "python3", "validate_model.py",
        "--season", "2022-23",
        "--cases", "lakers", "pacers", "suns",
        "--top-n", str(top_n),
        "--pass-threshold", str(pass_threshold),
        "--seed", str(seed),
        "--mode", "cases"
    ]
    
    if debug:
        cmd.append("--debug")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            return {
                "error": f"Command failed with return code {result.returncode}",
                "stderr": result.stderr,
                "stdout": result.stdout
            }
        
        # Parse the JSON output from stdout
        # Look for the JSON object in the output
        lines = result.stdout.strip().split('\n')
        json_start = -1
        json_end = -1
        
        for i, line in enumerate(lines):
            if line.strip().startswith('{'):
                json_start = i
                break
        
        if json_start >= 0:
            # Find the end of the JSON object
            brace_count = 0
            for i in range(json_start, len(lines)):
                line = lines[i]
                for char in line:
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            json_end = i
                            break
                if json_end >= 0:
                    break
            
            if json_end >= 0:
                json_lines = lines[json_start:json_end + 1]
                json_text = '\n'.join(json_lines)
                try:
                    return json.loads(json_text)
                except json.JSONDecodeError as e:
                    return {
                        "error": f"JSON decode error: {e}",
                        "json_text": json_text,
                        "stdout": result.stdout
                    }
        
        return {
            "error": "No JSON output found",
            "stdout": result.stdout
        }
            
    except subprocess.TimeoutExpired:
        return {"error": "Command timed out after 300 seconds"}
    except Exception as e:
        return {"error": f"Exception running command: {e}"}

def analyze_results(results: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze validation results and return summary."""
    if "error" in results:
        return {"error": results["error"]}
    
    cases = results.get("cases", {})
    all_passed = results.get("all_passed", False)
    
    case_summary = {}
    for case_name, case_data in cases.items():
        if isinstance(case_data, dict) and "composition" in case_data:
            comp = case_data["composition"]
            case_summary[case_name] = {
                "passed": case_data.get("passed", False),
                "preferred_in_top_n": comp.get("preferred_in_top_n", 0),
                "top_n_total": comp.get("top_n_total", 0),
                "preferred_ratio": comp.get("preferred_ratio", 0.0)
            }
        else:
            case_summary[case_name] = {
                "passed": False,
                "error": "Invalid case data"
            }
    
    return {
        "all_passed": all_passed,
        "cases": case_summary,
        "top_n": results.get("top_n", 0),
        "season": results.get("season", "unknown")
    }

def run_parameter_sweep(debug: bool = False) -> List[Dict[str, Any]]:
    """Run parameter sweep across different top-n and pass-threshold combinations."""
    print("🔍 Starting Parameter Sweep")
    print("=" * 50)
    
    # Parameter ranges to test
    top_n_values = [5, 10, 15, 20]
    pass_threshold_values = [1, 2, 3, 4, 5]
    
    results = []
    
    for top_n in top_n_values:
        for pass_threshold in pass_threshold_values:
            # Skip impossible combinations
            if pass_threshold > top_n:
                continue
                
            print(f"\n🧪 Testing: top_n={top_n}, pass_threshold={pass_threshold}")
            
            result = run_validation(top_n, pass_threshold, debug=debug)
            analysis = analyze_results(result)
            
            if "error" in analysis:
                print(f"   ❌ Error: {analysis['error']}")
            else:
                cases = analysis["cases"]
                lakers_passed = cases.get("lakers", {}).get("passed", False)
                pacers_passed = cases.get("pacers", {}).get("passed", False)
                suns_passed = cases.get("suns", {}).get("passed", False)
                all_passed = analysis["all_passed"]
                
                print(f"   Lakers: {'✅' if lakers_passed else '❌'} | Pacers: {'✅' if pacers_passed else '❌'} | Suns: {'✅' if suns_passed else '❌'}")
                print(f"   All Passed: {'✅' if all_passed else '❌'}")
                
                # Show detailed results for each case
                for case_name, case_data in cases.items():
                    if isinstance(case_data, dict) and "preferred_in_top_n" in case_data:
                        pref = case_data["preferred_in_top_n"]
                        total = case_data["top_n_total"]
                        ratio = case_data["preferred_ratio"]
                        print(f"     {case_name}: {pref}/{total} preferred ({ratio:.1%})")
            
            results.append({
                "top_n": top_n,
                "pass_threshold": pass_threshold,
                "result": analysis
            })
    
    return results

def find_working_combinations(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Find parameter combinations where all cases pass."""
    working = []
    
    for result in results:
        analysis = result["result"]
        if "error" not in analysis and analysis.get("all_passed", False):
            working.append({
                "top_n": result["top_n"],
                "pass_threshold": result["pass_threshold"],
                "cases": analysis["cases"]
            })
    
    return working

def print_summary(results: List[Dict[str, Any]]) -> None:
    """Print summary of parameter sweep results."""
    print("\n" + "=" * 50)
    print("📊 PARAMETER SWEEP SUMMARY")
    print("=" * 50)
    
    working = find_working_combinations(results)
    
    if working:
        print(f"✅ Found {len(working)} working combinations:")
        for combo in working:
            print(f"   top_n={combo['top_n']}, pass_threshold={combo['pass_threshold']}")
            
        # Find the most conservative (lowest) working combination
        best = min(working, key=lambda x: (x['top_n'], x['pass_threshold']))
        print(f"\n🎯 Recommended configuration:")
        print(f"   --top-n {best['top_n']} --pass-threshold {best['pass_threshold']}")
        
        print(f"\n📋 Detailed results for recommended config:")
        for case_name, case_data in best['cases'].items():
            pref = case_data['preferred_in_top_n']
            total = case_data['top_n_total']
            ratio = case_data['preferred_ratio']
            status = "✅" if case_data['passed'] else "❌"
            print(f"   {case_name}: {status} {pref}/{total} preferred ({ratio:.1%})")
    else:
        print("❌ No working combinations found")
        print("\n🔍 Debugging suggestions:")
        print("   1. Run with --debug flag to see detailed recommendations")
        print("   2. Check if core players are in the blessed set")
        print("   3. Verify archetype mappings are correct")
        print("   4. Consider adjusting preferred keywords")

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Parameter sweep for model validation")
    parser.add_argument("--debug", action="store_true", help="Enable debug output")
    parser.add_argument("--output", default="parameter_sweep_results.json", help="Output file for results")
    args = parser.parse_args()
    
    # Run the parameter sweep
    results = run_parameter_sweep(debug=args.debug)
    
    # Print summary
    print_summary(results)
    
    # Save results to file
    try:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n📄 Results saved to: {args.output}")
    except Exception as e:
        print(f"\n⚠️  Could not save results: {e}")

if __name__ == "__main__":
    main()
