import streamlit as st


def go(page):
    st.session_state.workspace_page = page


def welcome_journey(fin, df):
    steps = [('Record your first transaction', not df.empty, 'Transactions'), ('Set a monthly budget', bool(fin.records('budgets')), 'Budgets'), ('Give your savings a goal', bool(fin.records('goals')), 'Savings goals')]
    with st.expander('Your getting-started journey', expanded=not all(s[1] for s in steps)):
        st.progress(sum(s[1] for s in steps)/3, text=f'{sum(s[1] for s in steps)} of 3 foundations ready')
        cols = st.columns(3)
        for col, (title, done, page) in zip(cols, steps):
            with col:
                st.write(('✓ ' if done else '○ ') + title)
                st.button('Open ' + page, key='journey_'+page, on_click=go, args=(page,), width='stretch')
    left,right = st.columns([1.7,1])
    with left:
        st.markdown('<div class="pw-next"><span class="pw-tag">YOUR NEXT MONEY MOVE</span><h3>Make space for something better.</h3><p>Find spending you can change, choose your own pace, and create a savings plan that belongs to you.</p></div>', unsafe_allow_html=True)
        st.button('Discover where I can save →', type='primary', on_click=go, args=('Savings coach',), width='stretch')
    with right:
        st.markdown('<div class="pw-next pw-next-mint"><span class="pw-tag">TRY A DIFFERENT TOMORROW</span><h3>What if you spent a little less?</h3><p>Move a slider. See how small monthly changes could add up over time.</p></div>', unsafe_allow_html=True)
        st.button('Explore my possibilities →', on_click=go, args=('What-if Planner',), width='stretch')
    st.write('')
