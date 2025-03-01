1. Create fixed assets submenu



2. Create CashFlow Forecast
3. Create Index & Economic Rates
4. Create automatic transaction from a frequency
5. Order itens in BalanceSheet according to CODE

Now create a new menu and python file: calculate_depreciation.py.

in will have a search dialog for the accounting period
then it will look in fixed assets for fixed asset that are still active.
then it will go to depreciation schedule and try to find records for that specific accounting period start date and end date.
if it has, it will look at depreciation_expense column, if it has a value, it will ignore it. if not it will add to a list.
if it doesnt have a record in depreciation schedule at all, it will add to the list.

then it will calculate the depreciation for that specific interval of each asset and show to the user.

then the user can press a button to Generate Depreciation for Assets

This will create a new depreciation schedule for that specific period and 