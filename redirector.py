from django import shortcuts


def redirect_to(view_name, permanent=True, **defaults):
    """
    Constructs a view redirecting to the specified address.
    """

    def internal(request, **kwargs):
        for kv in defaults.items():
            kwargs.setdefault(*kv)
        return shortcuts.redirect(view_name, permanent=permanent, **kwargs)

    return internal
