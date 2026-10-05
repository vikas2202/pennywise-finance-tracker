"""Explainable spending reductions: estimates, never claimed realized savings."""
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
import math
import pandas as pd
from config.repository import Repository
from utils.validators import day

TIPS = {
    "Shopping": "Put optional purchases on a 48-hour wishlist. Review what you already own before buying.",
    "Entertainment": "Check unused subscriptions and try free activities. Keep the services you actually enjoy.",
    "Food & dining": "Plan meals around food already at home and compare takeaway with home-cooked options. Protect essential groceries.",
    "Transport": "Compare the total cost of your usual routes and combine errands where practical. Keep necessary journeys.",
    "Travel": "Compare flexible dates and set a trip spending limit before booking.",
    "Utilities": "Review unused add-ons and compare available plans, including switching costs. Keep essential services.",
}


@dataclass(frozen=True)
class SavingsOpportunity:
    category: str
    baseline_cents: int
    reduction_percent: int
    action: str

    @property
    def saving_cents(self):
        return int((Decimal(self.baseline_cents) * self.reduction_percent / 100).quantize(Decimal('1'), rounding=ROUND_HALF_UP))


class SavingsCoach:
    def opportunities(self, df, period, reductions=None):
        day(period + '-01')
        reductions = reductions or {}
        totals = df[(df.month == period) & (df.type == 'Expense')].groupby('category').amount_cents.sum()
        result = []
        for category, cents in totals.items():
            if category not in TIPS:
                continue
            percent = reductions.get(category, 0)
            if isinstance(percent, bool) or not isinstance(percent, int) or not 0 <= percent <= 50:
                raise ValueError('Reductions must be whole percentages from 0 to 50.')
            result.append(SavingsOpportunity(category, int(cents), percent, TIPS[category]))
        return sorted(result, key=lambda x: x.baseline_cents, reverse=True)

    @staticmethod
    def goal_months(remaining_cents, contribution_cents):
        if remaining_cents <= 0:
            return 0
        return math.ceil(remaining_cents / contribution_cents) if contribution_cents > 0 else None

    def recurring_candidates(self, df):
        expenses = df[df.type == 'Expense'].copy()
        expenses['label'] = expenses.description.str.strip().str.casefold()
        rows = []
        for (label, category), group in expenses.groupby(['label', 'category']):
            if not label or group.month.nunique() < 3:
                continue
            # Compare monthly totals, so split payments do not masquerade as subscriptions.
            sums = group.groupby('month').amount_cents.sum()
            median = float(sums.median())
            if median <= 0 or (sums.max() - sums.min()) / median > .2:
                continue
            rows.append({'Description':group.iloc[0].description, 'Category':category, 'Months observed':len(sums), 'Typical monthly amount':median / 100, 'Last recorded':group.date.max()})
        return pd.DataFrame(rows)


class SavingsPlanService:
    def __init__(self, store: Repository, user_id: str):
        self.store, self.uid = store, user_id

    def save(self, df, period, reductions):
        opportunities = SavingsCoach().opportunities(df, period, reductions)
        actions = [{'category':o.category, 'baseline_cents':o.baseline_cents, 'saving_cents':o.saving_cents, 'reduction_percent':o.reduction_percent, 'action':o.action, 'done':False} for o in opportunities if o.saving_cents > 0]
        if not actions:
            raise ValueError('Choose at least one reduction greater than zero.')
        return self.store.insert('saving_plans', {'user_id':self.uid, 'period':period, 'actions':actions, 'created_at':datetime.now(timezone.utc).isoformat()})

    def plans(self):
        return sorted(self.store.find('saving_plans', user_id=self.uid), key=lambda p:p['created_at'], reverse=True)

    def complete(self, plan_id, index, done):
        records = self.store.find('saving_plans', _id=plan_id, user_id=self.uid)
        if not records:
            raise ValueError('Plan not found.')
        actions = records[0]['actions']
        if not isinstance(index, int) or not 0 <= index < len(actions) or not isinstance(done, bool):
            raise ValueError('Invalid action update.')
        actions[index]['done'] = done
        self.store.update('saving_plans', plan_id, self.uid, {'actions':actions})

    def delete(self, plan_id):
        self.store.delete('saving_plans', plan_id, self.uid)
