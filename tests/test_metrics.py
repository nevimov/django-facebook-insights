"""Tests for the 'facebook_insights.metrics' module."""
# TODO:
# * Ensure that all test have appropriate names
# * Check/add docstrings where it's needed
# * Rearrange
from django.test import TestCase

from facebook_insights.exceptions import MetricsNotSpecified
from facebook_insights.metrics import fetch_metrics, Metric

TEST_PAGE_ID = '327730534261730'
TEST_POST_ID = '327730534261730_327732570928193'

class TestFetchMetric(TestCase):
    """Tests for the 'fetch_metric' function."""

    def test_raises_if_metrics_are_not_specified(self):
        """fetch_metrics() should raise an appropriate exception, if its
        argument 'metrics' evaluates to False (as it does in case the METRICS
        attribute of an Insights' child model is not set).
        """
        with self.assertRaises(MetricsNotSpecified):
            fetch_metrics(graph_id=TEST_PAGE_ID, metrics=None)
        with self.assertRaises(MetricsNotSpecified):
            fetch_metrics(graph_id=TEST_PAGE_ID, metrics=[])

    def test_fetch_page_metrics(self):
        """Test fetch_metrics() by fetching some page metrics."""
        page_metrics = fetch_metrics(
            graph_id=TEST_PAGE_ID,
            metrics=['page_impressions', 'page_impressions_unique']
        )
        self.assertIsInstance(page_metrics, dict)

        def test_page_metric(metric_name, period):
            self.assertIn(metric_name, page_metrics)
            metric = page_metrics[metric_name]
            self.assertIsInstance(metric, Metric)
            # 'page_impressions' and 'page_impressions_unique' (as most of
            # page metrics) should be available for the following periods:
            # 'day', 'week', 'days_28'.
            self.assertEqual(len(metric.values), 3)
            period_values = metric.values[period]
            # Each period should have values for 3 days
            self.assertEqual(len(period_values), 3)
            for item in period_values:
                self.assertEqual(len(item), 2)
                self.assertIn('value', item)
                self.assertIs(type(item['value']), int)
                self.assertIn('end_time', item)
                self.assertTrue(item['end_time'].startswith('20'))
                self.assertTrue(item['end_time'].endswith('+0000'))

        test_page_metric('page_impressions', 'day')
        test_page_metric('page_impressions', 'week')
        test_page_metric('page_impressions', 'days_28')
        test_page_metric('page_impressions_unique', 'day')
        test_page_metric('page_impressions_unique', 'week')
        test_page_metric('page_impressions_unique', 'days_28')

    def test_fetch_post_metrics(self):
        """Test fetch_metrics() by fetching some post metrics."""
        post_metrics = fetch_metrics(
            graph_id=TEST_POST_ID,
            metrics=['post_impressions', 'post_impressions_fan']
        )
        self.assertIsInstance(post_metrics, dict)

        def test_post_metric(metric_name):
            self.assertIn(metric_name, post_metrics)
            metric = post_metrics[metric_name]
            self.assertIsInstance(metric, Metric)
            # 'post_impressions' and 'post_impressions_fan' (as most of post
            # metrics) should be available for one period only ('lifetime').
            self.assertEqual(len(metric.values), 1)
            lifetime_values = metric.values['lifetime']
            # Lifetime metrics values always have one item (no records of
            # previous values as in the case of page metrics).
            self.assertEqual(len(lifetime_values), 1)
            item = lifetime_values[0]
            # These metrics don't have 'end_time'
            self.assertEqual(len(item), 1)
            self.assertIn('value', item)
            self.assertIs(type(item['value']), int)

        test_post_metric('post_impressions')
        test_post_metric('post_impressions_fan')


class TestMetric(TestCase):
    """Tests for the 'Metric' class."""

    def test__init__(self):
        values = {'lifetime': [{'value': 666}]}
        metric = Metric('post_impressions', values)
        self.assertEqual(metric.name, 'post_impressions')
        self.assertIs(metric.values, values)

    def test_get_value_of_metric_with_one_period(self):
        values = {'lifetime': [{'value': 666}]}
        metric = Metric('post_impressions', values)
        get_value = metric.get_value
        # By default, the last value should be returned
        self.assertEqual(get_value(period='lifetime'), {'value': 666})
        self.assertEqual(get_value(period='lifetime', extract=True), 666)
        # If a metric has only one period, then arg `period` can be omitted
        self.assertEqual(get_value(), {'value': 666})
        self.assertEqual(get_value(extract=True), 666)

    def test_get_value_of_metric_with_several_periods(self):
        values = {
            'day': [
                {'end_time': 't1', 'value': 1},
                {'end_time': 't2', 'value': 2},
                {'end_time': 't3', 'value': 3},
            ],
            'week': [
                {'end_time': 't1', 'value': 11},
                {'end_time': 't2', 'value': 12},
                {'end_time': 't3', 'value': 13},
            ],
            'days_28': [
                {'end_time': 't1', 'value': 100},
                {'end_time': 't2', 'value': 102},
                {'end_time': 't3', 'value': 103},
            ],
        }
        metric = Metric('page_impressions', values)
        get_value = metric.get_value

        self.assertEqual(get_value('day', index=0), values['day'][0])
        self.assertEqual(get_value('day', index=1), values['day'][1])
        self.assertEqual(get_value('day', index=2), values['day'][2])
        self.assertEqual(get_value('day'), values['day'][2])
        self.assertEqual(get_value('day', index=0, extract=True), 1)
        self.assertEqual(get_value('day', index=1, extract=True), 2)
        self.assertEqual(get_value('day', index=2, extract=True), 3)
        self.assertEqual(get_value('day', extract=True), 3)
        self.assertEqual(get_value('week', index=0), values['week'][0])
        self.assertEqual(get_value('week', index=1), values['week'][1])
        self.assertEqual(get_value('week', index=2), values['week'][2])
        self.assertEqual(get_value('week'), values['week'][2])
        self.assertEqual(get_value('week', index=0, extract=True), 11)
        self.assertEqual(get_value('week', index=1, extract=True), 12)
        self.assertEqual(get_value('week', index=2, extract=True), 13)
        self.assertEqual(get_value('week', extract=True), 13)
        self.assertEqual(get_value('days_28', index=0), values['days_28'][0])
        self.assertEqual(get_value('days_28', index=1), values['days_28'][1])
        self.assertEqual(get_value('days_28', index=2), values['days_28'][2])
        self.assertEqual(get_value('days_28'), values['days_28'][2])
        self.assertEqual(get_value('days_28', index=0, extract=True), 100)
        self.assertEqual(get_value('days_28', index=1, extract=True), 102)
        self.assertEqual(get_value('days_28', index=2, extract=True), 103)
        self.assertEqual(get_value('days_28', extract=True), 103)

    def test_get_all_values_of_metric_with_one_period(self):
        values = {'lifetime': [{'value': 666}]}
        metric = Metric('post_impressions', values)
        self.assertEqual(
            metric.get_all_values(index=0),
            {'lifetime': {'value': 666}}
        )
        self.assertEqual(
            metric.get_all_values(index=0, extract=True),
            {'lifetime': 666}
        )
        self.assertEqual(
            metric.get_all_values(),
            {'lifetime': {'value': 666}}
        )
        self.assertEqual(
            metric.get_all_values(extract=True),
            {'lifetime': 666}
        )

    def test_get_all_values_of_metric_with_several_periods(self):
        values = {
            'day': [
                {'end_time': 't1', 'value': 1},
                {'end_time': 't2', 'value': 2},
                {'end_time': 't3', 'value': 3},
            ],
            'week': [
                {'end_time': 't1', 'value': 11},
                {'end_time': 't2', 'value': 12},
                {'end_time': 't3', 'value': 13},
            ],
            'days_28': [
                {'end_time': 't1', 'value': 100},
                {'end_time': 't2', 'value': 102},
                {'end_time': 't3', 'value': 103},
            ],
        }
        metric = Metric('page_impressions', values)
        self.assertEqual(
            metric.get_all_values(index=0),
            {'day':     {'end_time': 't1', 'value': 1},
             'week':    {'end_time': 't1', 'value': 11},
             'days_28': {'end_time': 't1', 'value': 100}}
        )
        self.assertEqual(
            metric.get_all_values(index=1),
            {'day':     {'end_time': 't2', 'value': 2},
             'week':    {'end_time': 't2', 'value': 12},
             'days_28': {'end_time': 't2', 'value': 102}}
        )
        self.assertEqual(
            metric.get_all_values(index=2),
            {'day':     {'end_time': 't3', 'value': 3},
             'week':    {'end_time': 't3', 'value': 13},
             'days_28': {'end_time': 't3', 'value': 103}}
        )
        self.assertEqual(
            metric.get_all_values(),
            {'day':     {'end_time': 't3', 'value': 3},
             'week':    {'end_time': 't3', 'value': 13},
             'days_28': {'end_time': 't3', 'value': 103}}
        )
        self.assertEqual(
            metric.get_all_values(index=0, extract=True),
            {'day': 1, 'week': 11, 'days_28': 100}
        )
        self.assertEqual(
            metric.get_all_values(index=1, extract=True),
            {'day': 2, 'week': 12, 'days_28': 102}
        )
        self.assertEqual(
            metric.get_all_values(index=2, extract=True),
            {'day': 3, 'week': 13, 'days_28': 103}
        )
        self.assertEqual(
            metric.get_all_values(extract=True),
            {'day': 3, 'week': 13, 'days_28': 103}
        )
