"""Tools to fetch and extract Facebook Insights metrics.

>>> graph_id = '1234567890'
>>> metrics = ['page_impressions', 'page_engaged_users']
>>> page_metrics = fetch_metrics(graph_id, metrics)
>>> page_impressions = page_metrics['page_impressions']
>>> page_impressions.values
{'day': [
    {'end_time': '2016-11-15T08:00:00+0000', 'value': 0},
    {'end_time': '2016-11-16T08:00:00+0000', 'value': 1},
    {'end_time': '2016-11-17T08:00:00+0000', 'value': 2},
 ],
 'week': [
    {'end_time': '2016-11-15T08:00:00+0000', 'value': 10},
    {'end_time': '2016-11-16T08:00:00+0000', 'value': 11},
    {'end_time': '2016-11-17T08:00:00+0000', 'value': 12},
 ],
 'days_28': [
     {'end_time': '2016-11-15T08:00:00+0000', 'value': 100},
     {'end_time': '2016-11-16T08:00:00+0000', 'value': 101},
     {'end_time': '2016-11-17T08:00:00+0000', 'value': 102},
 ]
}
>>> page_impressions.get_value('day')
{'end_time': '2016-11-17T08:00:00+0000', 'value': 2}
>>> page_impressions.get_value('day', extract=True)
2
>>> page_impressions.get_value('week', index=0)
{'end_time': '2016-11-15T08:00:00+0000', 'value': 10}
>>> page_impressions.get_value('week', index=0, extract=True)
10
>>> get_all_values()
{'day':     {'end_time': '2016-11-17T08:00:00+0000', 'value': 2},
 'week':    {'end_time': '2016-11-17T08:00:00+0000', 'value': 12},
 'days_28': {'end_time': '2016-11-17T08:00:00+0000', 'value': 102}}
>>> get_all_values(extract=True)
{'day': 2, 'week': 12, 'days_28': 102}
>>> get_all_values(index=0, extract=True)
{'day': 0, 'week': 10, 'days_28': 100}

"""
import json

from django.conf import settings
from facebook import GraphAPI, GraphAPIError

from facebook_insights.exceptions import EmptyData, MetricsNotSpecified

__all__ = ['fetch_metrics', 'Metric']

access_token = settings.FACEBOOK_INSIGHTS_ACCESS_TOKEN
api_version = getattr(settings, 'FACEBOOK_INSIGHTS_API_VERSION', None)
graph_api = GraphAPI(access_token=access_token, version=api_version)


def fetch_metrics(graph_id, metrics):
    """Fetch Facebook Insights metrics for an object with a given id.

    Parameters
    ----------
    graph_id : str
        The Facebook ID of a Graph API object.
    metrics : iterable of str
        The object's metrics to fetch (e.g. 'page_engaged_users').

    Returns
    -------
    dict
        A dictionary of mappings between metric names and instances
        of class 'Metric'.

    """
    if not metrics:
        raise MetricsNotSpecified('Specify metrics you want to fetch.')
    batch = []
    for metric in metrics:
        request_data = {
            'method': 'GET',
            'relative_url': '{}/insights/{}/'.format(graph_id, metric)
        }
        batch.append(request_data)
    batch_response = graph_api.put_object(
        parent_object='/',
        connection_name='',
        batch=json.dumps(batch),
    )
    extracted_metrics = {}
    for response in batch_response:
        body = json.loads(response['body'])
        # (nevimov/2016-11-09): Currently facebook-sdk is not
        # able to catch errors in responses to batch requests, so
        # we have to take care of those ourselves.
        if 'error' in body:
            raise GraphAPIError(body)
        data = body['data']
        if not data:
            raise EmptyData
        rearranged_values = {}
        for datum in data:
            name = datum['name']
            period = datum['period']
            rearranged_values[period] = datum['values']
        extracted_metrics[name] = Metric(name, rearranged_values)
    return extracted_metrics


class Metric(object):
    """A Facebook Insights metric.

    Parameters
    ----------
    name : str
        The name of a metric (e.g. 'post_impressions' or 'page_engaged_users').
    values : dict of list of dict
        Values to associate with the metric. Must be a dictionary of mappings
        between periods ('day', 'week', 'days_28', 'lifetime') and lists of
        their respective values, for example:

        # The format typical for post metrics
        {'lifetime': [{'value': 1000}]}

        # The format typical for page metrics
        {'day': [
            {'end_time': '2016-11-15T08:00:00+0000', 'value': 0},
            {'end_time': '2016-11-16T08:00:00+0000', 'value': 1},
            {'end_time': '2016-11-17T08:00:00+0000', 'value': 2},
         ],
         'week': [
            {'end_time': '2016-11-15T08:00:00+0000', 'value': 10},
            {'end_time': '2016-11-16T08:00:00+0000', 'value': 11},
            {'end_time': '2016-11-17T08:00:00+0000', 'value': 12},
         ],
         'days_28': [
             {'end_time': '2016-11-15T08:00:00+0000', 'value': 100},
             {'end_time': '2016-11-16T08:00:00+0000', 'value': 101},
             {'end_time': '2016-11-17T08:00:00+0000', 'value': 102},
         ]}

    Attributes
    ----------
    name : str
        The name of the metric.
    values : list of dict of list
        The values associated with the metric.

    """

    def __init__(self, name, values):
        self.name = name
        self.values = values

    def get_value(self, period=None, index=-1, extract=False):
        """Get the metric's value for a given period.

        Parameters
        ----------
        period: {None, 'day', 'week', 'days_28', 'lifetime'}
            A period for which you want to get the value.
            Can be omitted for metrics available only for one period
            (e.g. all the post_impressions_* metrics).
        index : int
            For many metrics (e.g. most of page metrics) Facebook sends
            values for 3 consecutive days. By default this method returns
            the last value. If you want to get a previous value, pass
            `index` in range from 0 to 2 (or from -1 to -3).
        extract : bool
            By default the return value is a dictionary containing key
            'value' (most of page metrics also have 'end_time').
            If `extract` is True, then simply the value associated with
            this key is returned.

        Returns
        -------
        The return value can be either:
        * dictionary containing one key, 'value' (most of post metrics)
        * dictionary containing two keys, 'value' and 'end_time'
          (most of page metrics)
        Pass `extract=True`, if you don't care about the 'end_time' and
        need only the value.

        """
        values = self.values
        if not period:
            if len(values) == 1:
                period = list(values.keys())[0]
            else:
                raise TypeError(
                    "Can't get a period. Argument 'period' can be omitted "
                    "only for metrics that have one period."
                )
        value = values[period][index]
        if extract:
            return value['value']
        return value

    def get_all_values(self, index=-1, extract=False):
        """Get values for all periods.

        Parameters
        ----------
        Arguments `index` and `extract` have the same meaning as for
        get_value().

        Returns
        -------
        dict
            A mapping of periods to values.

        """
        all_values = {}
        for period in self.values:
            all_values[period] = self.get_value(period, index, extract)
        return all_values
