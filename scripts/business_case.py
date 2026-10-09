"""Projected business value calculator. Change any assumption from the command line.

python scripts/business_case.py
python scripts/business_case.py --properties 100 --lookups 60 --wage 22
"""

import argparse


def project(properties, lookups, minutes_saved, wage, wrong_per_week, comp_cost, cost_per_question, hosting_per_year):
    hours = properties * lookups * minutes_saved / 60 * 365
    labor = hours * wage
    refunds = properties * wrong_per_week * 52 * comp_cost
    questions = properties * lookups * 365
    run_cost = questions * cost_per_question + hosting_per_year
    value = labor + refunds
    return {
        "Staff hours saved per year": f"{hours:,.0f}",
        "Value of staff time": f"${labor:,.0f}",
        "Fewer refunds from wrong answers": f"${refunds:,.0f}",
        "Total projected value per year": f"${value:,.0f}",
        "Running cost per year (AI + hosting)": f"${run_cost:,.0f}",
        "Net value per year": f"${value - run_cost:,.0f}",
        "Return on running cost": f"{value / run_cost:,.0f}x",
    }


SCENARIOS = {
    # name: (lookups per day, minutes saved, wrong answers per week)
    "Pessimistic": (20, 1.0, 0.5),
    "Base": (40, 2.5, 1.0),
    "Optimistic": (60, 3.5, 2.0),
}


def scenarios(a):
    print(f"\nScenarios for {a.properties} properties (assumptions, not measured results)\n")
    header = f"  {'Scenario':<12} {'Lookups/day':>11} {'Min saved':>9} {'Wrong/wk':>8} {'Value/yr':>12} {'Net/yr':>12}"
    print(header)
    print("  " + "-" * (len(header) - 2))
    for name, (lookups, minutes, wrong) in SCENARIOS.items():
        r = project(a.properties, lookups, minutes, a.wage, wrong, a.comp_cost, a.cost_per_question, a.hosting)
        value, net = r["Total projected value per year"], r["Net value per year"]
        print(f"  {name:<12} {lookups:>11} {minutes:>9} {wrong:>8} {value:>12} {net:>12}")
    print()


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--properties", type=int, default=2)
    p.add_argument("--lookups", type=float, default=40, help="policy lookups per property per day")
    p.add_argument("--minutes-saved", type=float, default=2.5, help="minutes saved per lookup")
    p.add_argument("--wage", type=float, default=20, help="front-desk cost per hour, USD")
    p.add_argument("--wrong-per-week", type=float, default=1, help="wrong answers causing a refund, per property")
    p.add_argument("--comp-cost", type=float, default=75, help="average refund or comp, USD")
    p.add_argument("--cost-per-question", type=float, default=0.003, help="AI cost per question, USD")
    p.add_argument("--hosting", type=float, default=240, help="hosting per year, USD")
    p.add_argument("--scenarios", action="store_true", help="show pessimistic, base and optimistic cases")
    a = p.parse_args()

    if a.scenarios:
        scenarios(a)
        return

    result = project(
        a.properties, a.lookups, a.minutes_saved, a.wage, a.wrong_per_week, a.comp_cost, a.cost_per_question, a.hosting
    )
    print(f"\nProjected value for {a.properties} properties (assumptions, not measured results)\n")
    width = max(len(k) for k in result)
    for key, value in result.items():
        print(f"  {key:<{width}}  {value}")
    print()


if __name__ == "__main__":
    main()
