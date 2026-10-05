# Savings coach and new-user experience

## Walkthrough

1. Open the app and select Explore a live demo. No account is created; fictional records live only in that Streamlit session.
2. On Overview, use Discover where I can save to open Savings coach.
3. Select a reporting month. Prefer a completed month with complete records.
4. Choose realistic reduction percentages using the category sliders. All start at zero; no reduction is assumed for the user.
5. Compare baseline spending with the selected plan. Inspect the monthly reduction, the illustrative repeated annual amount, and the goal timeline.
6. Save the plan, open My action plans, and mark actions you have tried. Completion tracks behavior, not actual saved money.
7. Review possible repeated payments under Recurring spending. Verify whether each payment remains active and necessary.
8. Exit demo to discard its state and create a real account. Demo actions do not transfer to the real account.

## Business logic

`SavingsOpportunity` is an immutable value object. `SavingsCoach` groups the reporting month's expenses by category and creates suggestions only for six supported categories. Health, housing, and education are excluded from automatic reduction prompts. Suggestions do not establish whether a particular purchase is optional.

Reduction = recorded category expense multiplied by the user's percentage, rounded half-up to one paisa. Annual potential = monthly potential multiplied by 12, with no assumed investment return. The goal horizon rounds up remaining goal amount divided by the selected monthly reduction. Zero contributions produce no estimate; completed goals return zero months. The goal itself is not modified.

`SavingsPlanService` stores snapshots in a new `saving_plans` collection with owner, baseline month, timestamp, and action records. It verifies ownership for reads, updates, and deletion. A completed checkbox changes only its action state. Snapshot baseline values do not change when old transactions are later edited.

Recurring candidates require the same normalized description and category across three distinct months, with the range of monthly sums no greater than 20% of the median. The tool uses all recorded history and displays the latest date. It does not require consecutive months, establish a current subscription, or imply a bill should be canceled. Recurring amounts are not added to savings estimates, avoiding double counting.

## Privacy and data preservation

`DemoRepository` implements the repository interface using per-session memory and defensive copies. It is separate from SQLite and MongoDB, is never globally cached, and is discarded when the visitor exits the demo. Existing user collections and transactions do not require migration. The new collection receives an owner index in MongoDB.

## Limits and guidance

Incomplete records, unusually expensive baseline months, and changes in circumstances affect usefulness. Users choose whether changes are appropriate; estimates are neither guaranteed nor verified savings. No financial advice model, investment recommendation, bank transfer, subscription cancellation, or external AI service is involved.

The general track-review-plan approach is informed by the [Consumer Financial Protection Bureau spending tracker guidance](https://www.consumerfinance.gov/archive/blog/track-your-spending-with-this-easy-tool/). Category prompts and percentage calculations are application rules, not claims of validated savings outcomes.

## Verification

Tests cover exact rounding, percentage bounds, essential-category exclusions, sparse and inconsistent recurrence histories, goal horizon boundaries, owner isolation and plan updates in SQLite/MongoDB test-double/demo repositories, demo session separation, and end-to-end navigation and action completion.
