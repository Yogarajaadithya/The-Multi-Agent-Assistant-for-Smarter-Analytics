"""Quick integration test for the simulation agent backend wiring."""
import sys, asyncio
sys.path.insert(0, ".")

from app.services.multi_agent_system import initialize_llm
from app.services.simulation_agent import simulation_agent


async def test_hr():
    llm = initialize_llm()
    r = await simulation_agent(
        "What if we give everyone a 10% salary raise?",
        llm,
        dataset="hr_data",
        verbose=True,
    )
    assert r["success"], f"Failed: {r.get('error')}"
    print(f"\n--- HR (whatif) ---")
    print(f"  Sim type : {r['simulation_type']}")
    print(f"  Model    : {r['model_name']}")
    print(f"  Baseline : {r['baseline']['attrition_rate']*100:.1f}%")
    print(f"  Delta    : {r['delta']['attrition_rate_change']*100:+.2f} pp")
    print(f"  Saved    : {r['delta']['employees_saved']} employees")
    print(f"  Viz      : {r.get('visualization') is not None}")
    print(f"  Insights : {bool(r.get('insights'))}")


async def test_sales():
    llm = initialize_llm()
    r = await simulation_agent(
        "Compare: 5% price increase vs 10% discount reduction",
        llm,
        dataset="sales_data",
        verbose=True,
    )
    assert r["success"], f"Failed: {r.get('error')}"
    print(f"\n--- Sales (multi_scenario) ---")
    print(f"  Sim type : {r['simulation_type']}")
    print(f"  Model    : {r['model_name']}")
    print(f"  Baseline : €{r['baseline']['mean_revenue']:.2f} mean")
    print(r["comparison_table"].to_string(index=False))
    print(f"  Viz      : {r.get('visualization') is not None}")
    print(f"  Insights : {bool(r.get('insights'))}")


async def test_planner_routing():
    """Test that planner correctly classifies SIMULATE questions."""
    from app.services.planner_agent import planner_agent
    llm = initialize_llm()
    plan = await planner_agent(
        "What if we increase salary by 20% for the Sales department?", llm
    )
    print(f"\n--- Planner routing test ---")
    print(f"  Question type : {plan['question_type']}")
    print(f"  Agents        : {plan.get('agents_to_call')}")
    print(f"  Dataset guess : {plan.get('dataset')}")
    assert plan["question_type"] == "SIMULATE", (
        f"Expected SIMULATE, got {plan['question_type']}"
    )
    print("  ✅ Correctly routed to SIMULATE")


if __name__ == "__main__":
    print("=" * 60)
    print("SIMULATION AGENT INTEGRATION TESTS")
    print("=" * 60)
    asyncio.run(test_hr())
    asyncio.run(test_sales())
    asyncio.run(test_planner_routing())
    print("\n✅ All tests passed!")
