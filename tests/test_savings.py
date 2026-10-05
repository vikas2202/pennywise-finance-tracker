import pytest
import mongomock
from config.database import Store
from config.demo import DemoRepository
from services.analytics import frame
from services.savings import SavingsCoach, SavingsPlanService


def records():
    return frame([dict(_id=str(i), date=f'2026-0{i+1}-05', type='Expense', category='Shopping', description='Subscription', amount_cents=10005) for i in range(3)])


def test_reductions_exact_and_no_double_count():
    result = SavingsCoach().opportunities(records(), '2026-03', {'Shopping':10})
    assert result[0].saving_cents == 1001
    assert len(result) == 1
    assert SavingsCoach().opportunities(records(), '2026-04') == []
    assert SavingsCoach().opportunities(records(), '2026-03')[0].saving_cents == 0
    for invalid in [-1,51,1.5,True]:
        with pytest.raises(ValueError): SavingsCoach().opportunities(records(), '2026-03', {'Shopping':invalid})


def test_essential_categories_not_prompted():
    df=records()
    for category in ['Health','Housing','Education']:
        df['category']=category
        assert SavingsCoach().opportunities(df,'2026-03') == []


def test_recurring_detection_requires_three_months_and_consistent_totals():
    coach = SavingsCoach()
    assert len(coach.recurring_candidates(records())) == 1
    assert coach.recurring_candidates(records().iloc[:2]).empty
    df=records(); df.loc[0,'amount_cents']=100000
    assert coach.recurring_candidates(df).empty
    assert coach.recurring_candidates(frame([])).empty


def test_goal_horizon():
    assert SavingsCoach.goal_months(10001,1000) == 11
    assert SavingsCoach.goal_months(100,0) is None
    assert SavingsCoach.goal_months(0,0) == 0


@pytest.mark.parametrize('backend',['sqlite','mongodb','demo'])
def test_plan_persistence_and_account_isolation(tmp_path,backend):
    store = DemoRepository() if backend=='demo' else Store(backend, tmp_path/'savings.db', mongomock.MongoClient().finance if backend=='mongodb' else None)
    a,b = SavingsPlanService(store,'a'),SavingsPlanService(store,'b')
    with pytest.raises(ValueError): a.save(records(),'2026-03',{})
    plan=a.save(records(),'2026-03',{'Shopping':10})
    assert b.plans()==[]
    with pytest.raises(ValueError): b.complete(plan['_id'],0,True)
    with pytest.raises(ValueError): b.delete(plan['_id'])
    a.complete(plan['_id'],0,True)
    assert a.plans()[0]['actions'][0]['done']
    a.complete(plan['_id'],0,False)
    assert not a.plans()[0]['actions'][0]['done']
    a.delete(plan['_id'])
    assert a.plans()==[]


def test_demo_repository_copy_and_session_isolation():
    a,b=DemoRepository(),DemoRepository()
    original={'user_id':'demo','actions':[{'done':False}]}
    doc=a.insert('saving_plans',original)
    doc['actions'][0]['done']=True
    assert not a.find('saving_plans')[0]['actions'][0]['done']
    assert b.find('saving_plans') == []
