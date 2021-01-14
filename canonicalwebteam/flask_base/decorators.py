def exclude_xframe_options_header(func):
    func._exclude_xframe_options_header = True
    return func
