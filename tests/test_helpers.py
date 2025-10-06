def get_request_functions_names(functions):
    # "None" gets the application scoped functions
    # the blueprint functions are the ones that are named
    return [function.__name__ for function in functions.get(None, [])]
