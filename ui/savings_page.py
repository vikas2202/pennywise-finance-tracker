from datetime import date
import pandas as pd
import plotly.express as px
import streamlit as st
from services.savings import SavingsCoach, SavingsPlanService
from ui.pages import Page, plot
from ui.screens import attempt, cash, safe_csv
from ui.theme import section_intro


class SavingsPage(Page):
    def __init__(self, coach=None):
        self.coach = coach or SavingsCoach()

    def render(self, context):
        df, period = context.data, context.period
        service = SavingsPlanService(context.finance.store, context.finance.uid)
        discover, recurring, plans = st.tabs(['Find your savings', 'Recurring spending', 'My action plans'])
        with discover:
            section_intro('↗', 'Where could your money go further?', 'Choose the changes that fit your life. See their impact before committing.')
            st.caption(f'Baseline: recorded expenses in {period}. Missing records and partial months reduce the usefulness of estimates. No spending is automatically classified as unnecessary.')
            if period >= date.today().strftime('%Y-%m'):
                st.info('This month may be incomplete. Select a completed reporting month in the sidebar for a more useful baseline.')
            choices = self.coach.opportunities(df, period)
            if not choices:
                st.info('Record expenses in Shopping, Entertainment, Food & dining, Transport, Travel, or Utilities to explore possible changes. Health, housing, and education are excluded from automatic reduction prompts.')
            reductions = {}
            for o in choices:
                with st.container(border=True):
                    left,right = st.columns([1.7,1])
                    with left:
                        st.subheader(o.category)
                        st.write(o.action)
                        st.caption(f'Recorded baseline: {cash(o.baseline_cents / 100)}')
                    with right:
                        reductions[o.category] = st.slider(f'{o.category} reduction (%)', 0, 50, 0, step=5, key=f'cut_{context.finance.uid}_{period}_{o.category}')
            selected = self.coach.opportunities(df, period, reductions)
            savings = sum(o.saving_cents for o in selected)
            if choices:
                a,b,c = st.columns(3)
                a.metric('Potential monthly reduction', cash(savings/100))
                b.metric('If repeated for 12 months', cash(savings*12/100))
                c.metric('Actions selected', sum(o.saving_cents > 0 for o in selected))
                st.caption('Hypothetical reductions based on your choices, not guaranteed or already saved money. Annual figures assume the same spending and changes repeat every month.')
                rows = pd.DataFrame([{'Category':o.category,'Current spending':o.baseline_cents/100,'After your change':(o.baseline_cents-o.saving_cents)/100} for o in selected])
                plot(px.bar(rows, x='Category', y=['Current spending','After your change'], barmode='group', color_discrete_map={'Current spending':'#c3b8e8','After your change':'#14b8a6'}, labels={'value':'Amount (INR)'}))
                if st.button('Save my savings plan', type='primary', disabled=savings == 0):
                    attempt(lambda: service.save(df, period, reductions))
                st.download_button('Download my savings breakdown', safe_csv(rows), 'savings-breakdown.csv', 'text/csv')
                goals = context.finance.records('goals')
                if goals:
                    st.subheader('Give this money a purpose')
                    goal = st.selectbox('Put potential savings toward', goals, format_func=lambda g:g['name'])
                    months = self.coach.goal_months(goal['target_cents']-goal['current_cents'], savings)
                    if months == 0:
                        st.success('This goal is already complete.')
                    elif months is None:
                        st.info('Choose a reduction above to estimate a goal timeline.')
                    else:
                        st.info(f'At {cash(savings/100)} per month, this goal could take about {months} months using only these additional contributions. Assumes consistent saving and no interest.')
                    st.caption('This preview does not transfer money or update your goal balance.')
            with st.expander('Learn the method'):
                st.write('Track spending, distinguish obligations from optional purchases, then choose realistic changes. The app supplies arithmetic and prompts; you decide what is affordable and necessary.')
                st.markdown('[Spending tracker guidance — Consumer Financial Protection Bureau](https://www.consumerfinance.gov/archive/blog/track-your-spending-with-this-easy-tool/)')
        with recurring:
            section_intro('◎', 'Small repeats deserve a second look', 'Review possible recurring payments before deciding which ones still serve you.')
            candidates = self.coach.recurring_candidates(df)
            st.caption('Matches the same description and category in at least three months, with monthly totals varying by no more than 20% of their median. Uses all history. Rent and essential bills may appear; these are not confirmed subscriptions or cancellation recommendations.')
            if candidates.empty:
                st.info('No repeated payments meet the rule yet. Consistent descriptions and several months of records help.')
            else:
                st.dataframe(candidates, hide_index=True, width='stretch')
                st.write('Check whether each payment is still active, used, and necessary. Verify renewal terms with the provider before making changes. These amounts are not added to your savings estimates, avoiding double counting.')
        with plans:
            saved = service.plans()
            if not saved:
                st.info('Your saved plans will appear here. Start in “Find your savings”.')
            for plan in saved:
                with st.expander(f"Plan from {plan['period']} · {plan['created_at'][:10]}"):
                    completed = sum(a['done'] for a in plan['actions'])
                    st.progress(completed/len(plan['actions']), text=f'{completed} of {len(plan["actions"])} actions completed')
                    for index, action in enumerate(plan['actions']):
                        value = st.checkbox(f"{action['category']} · try {action['reduction_percent']}% less · potential {cash(action['saving_cents']/100)}", value=action['done'], key=f"action_{plan['_id']}_{index}")
                        if value != action['done']:
                            attempt(lambda: service.complete(plan['_id'], index, value))
                        st.caption(action['action'])
                    st.caption('Completion records a habit you tried. It does not verify savings or modify transactions.')
                    confirm = st.checkbox('Confirm plan deletion', key=f"confirm_plan_{plan['_id']}")
                    if st.button('Delete plan', key=f"delete_plan_{plan['_id']}", disabled=not confirm):
                        attempt(lambda: service.delete(plan['_id']))
