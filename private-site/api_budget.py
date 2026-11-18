"""Pure quota guard for future CBBD refresh jobs; performs zero network requests.

The free CFBD/CBBD quota is shared. A refresh must check /info first (free)
and reserve capacity for football. No API fetcher or publishing is enabled here.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Budget:
    remaining_calls: int
    planned_calls: int
    football_reserve: int = 500
    safety_reserve: int = 100
    max_calls_per_refresh: int = 12


def permit_refresh(budget: Budget) -> bool:
    values = (budget.remaining_calls, budget.planned_calls,
              budget.football_reserve, budget.safety_reserve,
              budget.max_calls_per_refresh)
    if any(type(x) is not int or x < 0 for x in values):
        return False
    return (0 < budget.planned_calls <= budget.max_calls_per_refresh
            and budget.remaining_calls - budget.planned_calls
            >= budget.football_reserve + budget.safety_reserve)
