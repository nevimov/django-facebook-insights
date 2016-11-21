__all__ = ['MetricsNotSpecified', 'EmptyData', 'MissingField']


class InsightsException(Exception):
    """Base class for the app's exceptions."""


class MetricsNotSpecified(InsightsException):
    """The code attempts to make a request to Facebook without specifying
    any metrics.
    """


class EmptyData(InsightsException):
    """The Facebook response contains key "data", but the associated
    array is empty.  This can happen, for instance, if the page has
    less than 30 likes or your app doesn't have permissions required
    to access its insights.
    """


class MissingField(InsightsException):
    """The model doesn't define a field for one of requested metrics."""
