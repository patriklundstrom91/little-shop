def get_bag_filter(request):
    """
    Returns a dict to filter BagItem objects for current user or session.
    """
    if request.user.is_authenticated:
        return {'user': request.user}
    else:
        if not request.session.session_key:
            request.session.create()
        return {'session_key': request.session.session_key}
