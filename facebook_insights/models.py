import json
import re

from django.db import models
from django.utils.encoding import python_2_unicode_compatible

from facebook_insights.metrics import fetch_metrics

__all__ = ['Insights']


@python_2_unicode_compatible
class Insights(models.Model):
    """The base class for all models storing Facebook Insights metrics."""
    METRICS = None
    """iterable: A list of metrics you're interested in."""
    GRAPH_ID_FIELD = 'graph_id'
    """str: The name of the field that stores the Facebook ID of the
    object for which you're retrieving metrics.
    """
    RELATED_OBJECT_FIELD = None
    """str: If the field specified in GRAPH_ID_FIELD is stored on a
    related object, then this attribute should be set to the name of
    the field referencing the related object.
    """
    REMOVE_PREFIX = True
    """
    All metrics are prepended with the name of the object they correspond to
    (e.g. 'page_' in 'page_engaged_users' or 'post_' in 'post_impressions').
    If True, then get_field_name() will remove this prefix to get the name
    of the field that should store a metric.
    """

    class Meta:
        abstract = True

    def __init__(self, *args, **kwargs):
        super(Insights, self).__init__(*args, **kwargs)
        self._graph_id = self.get_graph_id()
        try:
            all_field_names = [field.name for field in self._meta.get_fields()]
        except AttributeError:  # Django 1.7
            all_field_names = self._meta.get_all_field_names()
        self._all_field_names = all_field_names

    def __str__(self):
        return '<{class_name}: {pk}>'.format(
            class_name=self.__class__.__name__,
            pk=self._graph_id,
        )

    def __repr__(self):
        return '<{class_name}: {pk}>'.format(
            class_name=self.__class__.__name__,
            pk=self.pk,
        )


    def fetch(self, metrics=None):
        """Fetch metrics and put them into corresponding fields.

        Parameters
        ----------
        metrics : iterable of str
            List of metrics to fetch. If None (the default), then the
            value of the 'METRICS' attribute will be used.
            This may be useful, for example, to synchronize realtime
            metrics, but leave those updated once a day.

        """
        metrics_to_fetch = metrics or self.METRICS
        fetched_metrics = fetch_metrics(self._graph_id, metrics_to_fetch)
        for metric in fetched_metrics.values():
            field_name = self.get_field_name(metric)
            field_value = self.get_field_value(metric)
            if field_name not in self._all_field_names:
                raise AttributeError(
                    "Can't find a field for metric '{}'. "
                    "Expected field name '{}'."
                    "".format(metric.name, field_name)
                )
            setattr(self, field_name, field_value)

    def get_field_name(self, metric):
        """Get the name of the field that should store the metric."""
        field_name = metric.name
        if self.REMOVE_PREFIX:
            prefix_regex = r'^(page|post|domain)_'
            field_name = re.sub(prefix_regex, '', field_name)
        return field_name

    def get_field_value(self, metric):
        """Get the value for the field that should store the metric."""
        if len(metric.values) == 1:
            field_value = metric.get_value(extract=True)
        else:
            field_value = metric.get_all_values(extract=True)
        # Values that are not numbers are serialized into JSON
        if not isinstance(field_value, int):
            field_value = json.dumps(field_value)
        return field_value

    def get_graph_id(self):
        """Get graph ID of the object for which metrics are to be collected."""
        if self.RELATED_OBJECT_FIELD:
            related_object = getattr(self, self.RELATED_OBJECT_FIELD)
            return getattr(related_object, self.GRAPH_ID_FIELD)
        return getattr(self, self.GRAPH_ID_FIELD)
