from django.conf import settings


def convert(text, from_, to):
    if from_ == to:
        return text
    elif not settings.PANDOC['REQUIRED']:
        # TODO: Log that.
        return text

    import pypandoc  # Do not perform a global import.
    return pypandoc.convert_text(
        text,
        to,
        format=from_,
        filters=settings.PANDOC['FILTERS'],
        extra_args=settings.PANDOC['EXTRA_ARGS'],
    )
