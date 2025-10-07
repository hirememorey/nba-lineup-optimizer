"""
Ground Truth Validation for 2022-23 Data

This script tests the simple evaluator against known basketball outcomes
to validate that our implementation captures fundamental basketball principles
before attempting to reproduce the original paper.

Based on post-mortem insights, we focus on:
1. Westbrook Lakers failure (redundant ball handlers)
2. Westbrook Clippers success (better fit)
3. Other obvious basketball cases
"""

from simple_2022_23_evaluator import Simple2022_23Evaluator
import pandas as pd


def test_westbrook_cases():
    """Test the most obvious case: Westbrook Lakers failure vs Clippers success."""
    print("🏀 Testing Westbrook Cases (Lakers Failure vs Clippers Success)")
    print("=" * 70)
    
    evaluator = Simple2022_23Evaluator()
    
    # Get key players
    lebron = evaluator.get_player_by_name("LeBron James")
    ad = evaluator.get_player_by_name("Anthony Davis")
    westbrook = evaluator.get_player_by_name("Russell Westbrook")
    kawhi = evaluator.get_player_by_name("Kawhi Leonard")
    
    if not all([lebron, ad, westbrook, kawhi]):
        print("❌ Missing key players for Westbrook test")
        return False
    
    print(f"Key players loaded:")
    print(f"  LeBron: DARKO {lebron.darko:.2f} (Off: {lebron.offensive_darko:.2f}, Def: {lebron.defensive_darko:.2f})")
    print(f"  AD: DARKO {ad.darko:.2f} (Off: {ad.offensive_darko:.2f}, Def: {ad.defensive_darko:.2f})")
    print(f"  Westbrook: DARKO {westbrook.darko:.2f} (Off: {westbrook.offensive_darko:.2f}, Def: {westbrook.defensive_darko:.2f})")
    print(f"  Kawhi: DARKO {kawhi.darko:.2f} (Off: {kawhi.offensive_darko:.2f}, Def: {kawhi.defensive_darko:.2f})")
    
    # Test 1: Lakers lineup with Westbrook (should be low due to redundant ball handlers)
    print(f"\\n1. Lakers lineup with Westbrook (should be LOW due to redundant ball handlers):")
    
    # Find Lakers supporting players
    lakers_support = [p for p in evaluator.get_available_players() 
                     if p.player_name in ["Austin Reaves", "Rui Hachimura", "D'Angelo Russell", "Lonnie Walker", "Malik Beasley", "Jarred Vanderbilt"]][:3]
    
    if len(lakers_support) >= 2:
        lakers_with_westbrook = [lebron.player_id, ad.player_id, westbrook.player_id] + [p.player_id for p in lakers_support[:2]]
        lakers_result = evaluator.evaluate_lineup(lakers_with_westbrook)
        
        print(f"   Lineup: {[evaluator.get_player_by_id(pid).player_name for pid in lakers_with_westbrook]}")
        print(f"   Score: {lakers_result.predicted_outcome:.3f}")
        print(f"   Breakdown: {lakers_result.breakdown}")
        print(f"   Explanation: {lakers_result.basketball_explanation}")
        
        # Test 2: Lakers lineup without Westbrook (should be higher)
        print(f"\\n2. Lakers lineup WITHOUT Westbrook (should be HIGHER):")
        lakers_without_westbrook = [lebron.player_id, ad.player_id] + [p.player_id for p in lakers_support[:3]]
        if len(lakers_without_westbrook) == 5:
            lakers_no_wb_result = evaluator.evaluate_lineup(lakers_without_westbrook)
        else:
            print(f"   Not enough Lakers support players (need 3, got {len(lakers_support)})")
            return False
        
        print(f"   Lineup: {[evaluator.get_player_by_id(pid).player_name for pid in lakers_without_westbrook]}")
        print(f"   Score: {lakers_no_wb_result.predicted_outcome:.3f}")
        print(f"   Breakdown: {lakers_no_wb_result.breakdown}")
        print(f"   Explanation: {lakers_no_wb_result.basketball_explanation}")
        
        # Test 3: Clippers lineup with Westbrook (should be higher than Lakers)
        print(f"\\n3. Clippers lineup with Westbrook (should be HIGHER than Lakers):")
        
        clippers_support = [p for p in evaluator.get_available_players() 
                           if p.player_name in ["Paul George", "Ivica Zubac", "Marcus Morris", "Reggie Jackson", "Nicolas Batum"]][:4]
        
        if len(clippers_support) >= 4:
            clippers_with_westbrook = [kawhi.player_id] + [p.player_id for p in clippers_support]
            clippers_result = evaluator.evaluate_lineup(clippers_with_westbrook)
            
            print(f"   Lineup: {[evaluator.get_player_by_id(pid).player_name for pid in clippers_with_westbrook]}")
            print(f"   Score: {clippers_result.predicted_outcome:.3f}")
            print(f"   Breakdown: {clippers_result.breakdown}")
            print(f"   Explanation: {clippers_result.basketball_explanation}")
            
            # Compare results
            print(f"\\n📊 COMPARISON:")
            print(f"   Lakers WITH Westbrook:  {lakers_result.predicted_outcome:.3f}")
            print(f"   Lakers WITHOUT Westbrook: {lakers_no_wb_result.predicted_outcome:.3f}")
            print(f"   Clippers WITH Westbrook: {clippers_result.predicted_outcome:.3f}")
            
            # Validate ground truth
            lakers_improvement = lakers_no_wb_result.predicted_outcome - lakers_result.predicted_outcome
            clippers_vs_lakers = clippers_result.predicted_outcome - lakers_result.predicted_outcome
            
            print(f"\\n✅ GROUND TRUTH VALIDATION:")
            if lakers_improvement > 0:
                print(f"   ✅ Lakers improve without Westbrook (+{lakers_improvement:.3f})")
            else:
                print(f"   ❌ Lakers should improve without Westbrook (got {lakers_improvement:.3f})")
            
            if clippers_vs_lakers > 0:
                print(f"   ✅ Clippers better than Lakers with Westbrook (+{clippers_vs_lakers:.3f})")
            else:
                print(f"   ❌ Clippers should be better than Lakers with Westbrook (got {clippers_vs_lakers:.3f})")
            
            return lakers_improvement > 0 and clippers_vs_lakers > 0
    
    return False


def test_archetype_diversity():
    """Test that the evaluator recognizes different player archetypes."""
    print("\\n🏀 Testing Archetype Diversity Recognition")
    print("=" * 50)
    
    evaluator = Simple2022_23Evaluator()
    
    # Find players with different skill profiles
    players = evaluator.get_available_players()
    
    # Look for clear archetypes
    playmakers = [p for p in players if p.archetype_features['ASTPCT'] > 0.25 and p.archetype_features['DRIVES'] > 5][:2]
    shooters = [p for p in players if p.archetype_features['CS3PA'] > 2 and p.archetype_features['DRPTSPCT'] > 0.35][:2]
    bigs = [p for p in players if p.archetype_features['POSTUPS'] > 1 and p.archetype_features['PNTTOUCH'] > 3][:2]
    
    print(f"Found archetypes:")
    print(f"  Playmakers: {[p.player_name for p in playmakers]}")
    print(f"  Shooters: {[p.player_name for p in shooters]}")
    print(f"  Bigs: {[p.player_name for p in bigs]}")
    
    if len(playmakers) >= 2 and len(shooters) >= 2 and len(bigs) >= 1:
        # Test diverse lineup
        diverse_lineup = [playmakers[0].player_id, playmakers[1].player_id, 
                         shooters[0].player_id, shooters[1].player_id, bigs[0].player_id]
        
        diverse_result = evaluator.evaluate_lineup(diverse_lineup)
        print(f"\\nDiverse lineup score: {diverse_result.predicted_outcome:.3f}")
        print(f"Archetype diversity: {diverse_result.breakdown['archetype_diversity']:.3f}")
        print(f"Explanation: {diverse_result.basketball_explanation}")
        
        # Test redundant lineup (all playmakers)
        redundant_players = playmakers[:5] if len(playmakers) >= 5 else playmakers + [p for p in players if p not in playmakers][:5-len(playmakers)]
        redundant_lineup = [p.player_id for p in redundant_players]
        
        if len(redundant_lineup) == 5:
            redundant_result = evaluator.evaluate_lineup(redundant_lineup)
            print(f"\\nRedundant lineup score: {redundant_result.predicted_outcome:.3f}")
            print(f"Redundancy penalty: {redundant_result.breakdown['redundancy_penalty']:.3f}")
            print(f"Explanation: {redundant_result.basketball_explanation}")
            
            if diverse_result.predicted_outcome > redundant_result.predicted_outcome:
                print(f"✅ Diverse lineup outperforms redundant lineup")
                return True
            else:
                print(f"❌ Diverse lineup should outperform redundant lineup")
                return False
    
    return False


def test_skill_balance():
    """Test that the evaluator recognizes offensive/defensive balance."""
    print("\\n🏀 Testing Offensive/Defensive Balance")
    print("=" * 50)
    
    evaluator = Simple2022_23Evaluator()
    players = evaluator.get_available_players()
    
    # Find offensive and defensive specialists
    offensive_players = sorted([p for p in players if p.offensive_darko > 2.0], key=lambda x: x.offensive_darko, reverse=True)[:3]
    defensive_players = sorted([p for p in players if p.defensive_darko > 1.0], key=lambda x: x.defensive_darko, reverse=True)[:3]
    balanced_players = [p for p in players if 0.5 < p.offensive_darko < 2.0 and 0.5 < p.defensive_darko < 2.0][:5]
    
    print(f"Offensive specialists: {[p.player_name for p in offensive_players]}")
    print(f"Defensive specialists: {[p.player_name for p in defensive_players]}")
    print(f"Balanced players: {[p.player_name for p in balanced_players]}")
    
    if len(offensive_players) >= 3 and len(defensive_players) >= 2 and len(balanced_players) >= 5:
        # Test balanced lineup
        balanced_lineup = [p.player_id for p in balanced_players[:5]]
        balanced_result = evaluator.evaluate_lineup(balanced_lineup)
        
        print(f"\\nBalanced lineup score: {balanced_result.predicted_outcome:.3f}")
        print(f"Skill balance: {balanced_result.breakdown['skill_balance']:.3f}")
        print(f"Explanation: {balanced_result.basketball_explanation}")
        
        # Test imbalanced lineup (all offense)
        imbalanced_players = offensive_players[:5] if len(offensive_players) >= 5 else offensive_players + [p for p in players if p not in offensive_players][:5-len(offensive_players)]
        imbalanced_lineup = [p.player_id for p in imbalanced_players]
        
        if len(imbalanced_lineup) == 5:
            imbalanced_result = evaluator.evaluate_lineup(imbalanced_lineup)
        else:
            print(f"   Not enough offensive players (need 5, got {len(offensive_players)})")
            return False
        
        print(f"\\nImbalanced lineup score: {imbalanced_result.predicted_outcome:.3f}")
        print(f"Skill balance: {imbalanced_result.breakdown['skill_balance']:.3f}")
        print(f"Explanation: {imbalanced_result.basketball_explanation}")
        
        if balanced_result.predicted_outcome > imbalanced_result.predicted_outcome:
            print(f"✅ Balanced lineup outperforms imbalanced lineup")
            return True
        else:
            print(f"❌ Balanced lineup should outperform imbalanced lineup")
            return False
    
    return False


def run_comprehensive_validation():
    """Run all ground truth validation tests."""
    print("🏀 COMPREHENSIVE GROUND TRUTH VALIDATION")
    print("=" * 70)
    print("Testing fundamental basketball principles before paper reproduction...")
    
    results = []
    
    # Test 1: Westbrook cases (most important)
    print("\\n" + "="*70)
    results.append(("Westbrook Cases", test_westbrook_cases()))
    
    # Test 2: Archetype diversity
    print("\\n" + "="*70)
    results.append(("Archetype Diversity", test_archetype_diversity()))
    
    # Test 3: Skill balance
    print("\\n" + "="*70)
    results.append(("Skill Balance", test_skill_balance()))
    
    # Summary
    print("\\n" + "="*70)
    print("📊 VALIDATION SUMMARY")
    print("="*70)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\\n🎉 ALL TESTS PASSED! Ready to proceed with paper reproduction.")
        return True
    else:
        print("\\n⚠️  Some tests failed. Need to improve evaluator before paper reproduction.")
        return False


if __name__ == "__main__":
    run_comprehensive_validation()
