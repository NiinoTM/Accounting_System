# utils/depreciation_methods.py
def calculate_depreciation(method, cost, salvage_value, life=None, rate=None,
                          units_produced=None, total_units=None,
                          current_book_value=None, period=1): #Added period
    """
    Calculates depreciation for a given period using various methods.

    Args:
        method (str): The depreciation method.
        cost (float): Original cost.
        salvage_value (float): Salvage value.
        life (int, optional): Useful life in years.
        rate (float, optional): Depreciation rate (for declining balance methods).
        units_produced (int, optional): Units produced in the current period.
        total_units (int, optional): Total estimated units.
        current_book_value(float, optional): current value of the book
        period (int, optional): Current period for SYD calculation. Defaults to 1.

    Returns:
        float: The calculated depreciation amount for the period.  Returns 0 on invalid input.
        str: Error, if there is any.

    Raises:
        ValueError: If the depreciation method is invalid.
    """
    if cost <= 0 or salvage_value < 0 or cost < salvage_value:
        return 0, "invalid-input"

    if method == 'Straight-Line':
        if life is None or life <= 0:
            return 0, "invalid-input"
        return (cost - salvage_value) / life, None

    elif method == "Sum of the Years' Digit":
        if life is None or life <= 0:
            return 0, "invalid-input"
        if period > life: # handles the periods, and that its not bigger than life
            return 0, "invalid-period"
        syd = (life * (life + 1)) / 2
        return (cost - salvage_value) * (life - period + 1) / syd, None # removed remainig life

    elif method == 'Declining Balance':
        if rate is None or rate <= 0 or rate > 1 or current_book_value is None:
            return 0, "invalid-input"
        # Ensure depreciation doesn't go below salvage value
        depreciation_amount = current_book_value * rate
        if current_book_value - depreciation_amount < salvage_value:
            depreciation_amount = current_book_value - salvage_value
        return depreciation_amount, None

    elif method == 'Double-Declining Balance':
        if life is None or life <=0:
            return 0, "invalid-input"

        if rate is None:
          rate = (1 / life) * 2
        depreciation_amount = current_book_value * rate

        if current_book_value - depreciation_amount < salvage_value:
          depreciation_amount = current_book_value - salvage_value

        return depreciation_amount, None

    elif method == 'Units of Production':
        if units_produced is None or total_units is None or total_units <= 0:
            return 0, "invalid-input"
        if units_produced <0:
            return 0, "invalid-units"
        return (cost - salvage_value) * (units_produced / total_units), None
    else:
        return 0, "invalid-method"