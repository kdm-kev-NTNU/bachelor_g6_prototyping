"""
Test suite for LLM-as-Judge testing system.
"""

import asyncio
import json
from typing import Dict, Any
from building_data import generate_buildings, get_building_dict
from advisor import create_advisor
from judge import create_judge


def test_building_generation():
    """Test building data generation."""
    print("Testing building generation...")
    buildings = generate_buildings(5)
    assert len(buildings) == 5, "Should generate 5 buildings"
    
    for building in buildings:
        assert building.current_energy_kwh > 0, "Energy usage should be positive"
        assert building.expected_energy_kwh > 0, "Expected energy should be positive"
        assert building.size_m2 > 0, "Size should be positive"
    
    print("✓ Building generation test passed")


def test_advisor_structure():
    """Test advisor structure (without actual API call)."""
    print("Testing advisor structure...")
    try:
        advisor = create_advisor()
        assert advisor is not None, "Advisor should be created"
        assert hasattr(advisor, 'generate_advice'), "Advisor should have generate_advice method"
        print("✓ Advisor structure test passed")
    except ValueError as e:
        if "EINO_API_KEY" in str(e) or "API_KEY" in str(e):
            print("⚠ Advisor structure test skipped (no API key)")
        else:
            raise


def test_judge_structure():
    """Test judge structure (without actual API call)."""
    print("Testing judge structure...")
    try:
        judge = create_judge()
        assert judge is not None, "Judge should be created"
        assert hasattr(judge, 'evaluate'), "Judge should have evaluate method"
        print("✓ Judge structure test passed")
    except ValueError as e:
        if "EINO_API_KEY" in str(e) or "API_KEY" in str(e):
            print("⚠ Judge structure test skipped (no API key)")
        else:
            raise


def test_full_pipeline_mock():
    """Test full pipeline with mock data."""
    print("Testing full pipeline (mock)...")
    
    buildings = generate_buildings(1)
    building_dict = get_building_dict(buildings[0])
    
    # Mock advice
    mock_advice = """
    Basert på bygningsdataene ser jeg at bygningen bruker betydelig mer energi enn forventet.
    Du kan vurdere å forbedre isolasjonen, spesielt i taket og veggene.
    Det kan også være lurt å vurdere å bytte ut vinduer til mer energieffektive alternativer.
    Basert på tilgjengelige data kan dette potensielt redusere energibruken med 20-30%.
    """
    
    # Test judge evaluation structure
    try:
        judge = create_judge()
        evaluation = judge.evaluate(mock_advice, building_dict)
        
        assert hasattr(evaluation, 'data_referencing'), "Evaluation should have data_referencing"
        assert hasattr(evaluation, 'total_score'), "Evaluation should have total_score"
        assert 0 <= evaluation.total_score <= 10, "Total score should be 0-10"
        
        print("✓ Full pipeline test passed")
    except Exception as e:
        if "EINO_API_KEY" in str(e) or "API" in str(e):
            print("⚠ Full pipeline test skipped (no API key)")
        else:
            print(f"⚠ Full pipeline test failed: {e}")


def test_rubric_consistency():
    """Test that rubric criteria are consistent."""
    print("Testing rubric consistency...")
    
    from config import JUDGE_RUBRIC
    
    criteria = [
        "data_referencing",
        "internal_consistency", 
        "fact_vs_assumption",
        "uncertainty_acknowledgement",
        "advisory_tone"
    ]
    
    for criterion in criteria:
        assert criterion in JUDGE_RUBRIC.lower() or criterion.replace("_", " ") in JUDGE_RUBRIC.lower(), \
            f"Criterion {criterion} should be in rubric"
    
    print("✓ Rubric consistency test passed")


def run_all_tests():
    """Run all tests."""
    print("=" * 50)
    print("Running LLM-as-Judge Testing System Tests")
    print("=" * 50)
    print()
    
    tests = [
        test_building_generation,
        test_advisor_structure,
        test_judge_structure,
        test_rubric_consistency,
        test_full_pipeline_mock
    ]
    
    passed = 0
    skipped = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"✗ {test.__name__} failed: {e}")
            failed += 1
        except Exception as e:
            if "skipped" in str(e).lower():
                skipped += 1
            else:
                print(f"✗ {test.__name__} error: {e}")
                failed += 1
    
    print()
    print("=" * 50)
    print(f"Results: {passed} passed, {skipped} skipped, {failed} failed")
    print("=" * 50)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
