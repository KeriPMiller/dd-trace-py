from nose.tools import eq_, ok_

from .web.app import CustomDefaultHandler
from .utils import TornadoTestCase

from ddtrace.constants import SAMPLING_PRIORITY_KEY, ORIGIN_KEY, ANALYTICS_SAMPLE_RATE_KEY

from opentracing.scope_managers.tornado import TornadoScopeManager
from tests.opentracer.utils import init_tracer


class TestTornadoWeb(TornadoTestCase):
    """
    Ensure that Tornado web handlers are properly traced.
    """
    def test_success_handler(self):
        # it should trace a handler that returns 200
        response = self.fetch('/success/')
        eq_(200, response.code)

        traces = self.tracer.writer.pop_traces()
        eq_(1, len(traces))
        eq_(1, len(traces[0]))

        request_span = traces[0][0]
        eq_('tornado-web', request_span.service)
        eq_('tornado.request', request_span.name)
        eq_('http', request_span.span_type)
        eq_('tests.contrib.tornado.web.app.SuccessHandler', request_span.resource)
        eq_('GET', request_span.get_tag('http.method'))
        eq_('200', request_span.get_tag('http.status_code'))
        eq_('/success/', request_span.get_tag('http.url'))
        eq_(0, request_span.error)

    def test_nested_handler(self):
        # it should trace a handler that calls the tracer.trace() method
        # using the automatic Context retrieval
        response = self.fetch('/nested/')
        eq_(200, response.code)
        traces = self.tracer.writer.pop_traces()
        eq_(1, len(traces))
        eq_(2, len(traces[0]))
        # check request span
        request_span = traces[0][0]
        eq_('tornado-web', request_span.service)
        eq_('tornado.request', request_span.name)
        eq_('http', request_span.span_type)
        eq_('tests.contrib.tornado.web.app.NestedHandler', request_span.resource)
        eq_('GET', request_span.get_tag('http.method'))
        eq_('200', request_span.get_tag('http.status_code'))
        eq_('/nested/', request_span.get_tag('http.url'))
        eq_(0, request_span.error)
        # check nested span
        nested_span = traces[0][1]
        eq_('tornado-web', nested_span.service)
        eq_('tornado.sleep', nested_span.name)
        eq_(0, nested_span.error)
        # check durations because of the yield sleep
        ok_(request_span.duration >= 0.05)
        ok_(nested_span.duration >= 0.05)

    def test_exception_handler(self):
        # it should trace a handler that raises an exception
        response = self.fetch('/exception/')
        eq_(500, response.code)

        traces = self.tracer.writer.pop_traces()
        eq_(1, len(traces))
        eq_(1, len(traces[0]))

        request_span = traces[0][0]
        eq_('tornado-web', request_span.service)
        eq_('tornado.request', request_span.name)
        eq_('http', request_span.span_type)
        eq_('tests.contrib.tornado.web.app.ExceptionHandler', request_span.resource)
        eq_('GET', request_span.get_tag('http.method'))
        eq_('500', request_span.get_tag('http.status_code'))
        eq_('/exception/', request_span.get_tag('http.url'))
        eq_(1, request_span.error)
        eq_('Ouch!', request_span.get_tag('error.msg'))
        ok_('Exception: Ouch!' in request_span.get_tag('error.stack'))

    def test_http_exception_handler(self):
        # it should trace a handler that raises a Tornado HTTPError
        response = self.fetch('/http_exception/')
        eq_(501, response.code)

        traces = self.tracer.writer.pop_traces()
        eq_(1, len(traces))
        eq_(1, len(traces[0]))

        request_span = traces[0][0]
        eq_('tornado-web', request_span.service)
        eq_('tornado.request', request_span.name)
        eq_('http', request_span.span_type)
        eq_('tests.contrib.tornado.web.app.HTTPExceptionHandler', request_span.resource)
        eq_('GET', request_span.get_tag('http.method'))
        eq_('501', request_span.get_tag('http.status_code'))
        eq_('/http_exception/', request_span.get_tag('http.url'))
        eq_(1, request_span.error)
        eq_('HTTP 501: Not Implemented (unavailable)', request_span.get_tag('error.msg'))
        ok_('HTTP 501: Not Implemented (unavailable)' in request_span.get_tag('error.stack'))

    def test_http_exception_500_handler(self):
        # it should trace a handler that raises a Tornado HTTPError
        response = self.fetch('/http_exception_500/')
        eq_(500, response.code)

        traces = self.tracer.writer.pop_traces()
        eq_(1, len(traces))
        eq_(1, len(traces[0]))

        request_span = traces[0][0]
        eq_('tornado-web', request_span.service)
        eq_('tornado.request', request_span.name)
        eq_('http', request_span.span_type)
        eq_('tests.contrib.tornado.web.app.HTTPException500Handler', request_span.resource)
        eq_('GET', request_span.get_tag('http.method'))
        eq_('500', request_span.get_tag('http.status_code'))
        eq_('/http_exception_500/', request_span.get_tag('http.url'))
        eq_(1, request_span.error)
        eq_('HTTP 500: Server Error (server error)', request_span.get_tag('error.msg'))
        ok_('HTTP 500: Server Error (server error)' in request_span.get_tag('error.stack'))

    def test_sync_success_handler(self):
        # it should trace a synchronous handler that returns 200
        response = self.fetch('/sync_success/')
        eq_(200, response.code)

        traces = self.tracer.writer.pop_traces()
        eq_(1, len(traces))
        eq_(1, len(traces[0]))

        request_span = traces[0][0]
        eq_('tornado-web', request_span.service)
        eq_('tornado.request', request_span.name)
        eq_('http', request_span.span_type)
        eq_('tests.contrib.tornado.web.app.SyncSuccessHandler', request_span.resource)
        eq_('GET', request_span.get_tag('http.method'))
        eq_('200', request_span.get_tag('http.status_code'))
        eq_('/sync_success/', request_span.get_tag('http.url'))
        eq_(0, request_span.error)

    def test_sync_exception_handler(self):
        # it should trace a handler that raises an exception
        response = self.fetch('/sync_exception/')
        eq_(500, response.code)

        traces = self.tracer.writer.pop_traces()
        eq_(1, len(traces))
        eq_(1, len(traces[0]))

        request_span = traces[0][0]
        eq_('tornado-web', request_span.service)
        eq_('tornado.request', request_span.name)
        eq_('http', request_span.span_type)
        eq_('tests.contrib.tornado.web.app.SyncExceptionHandler', request_span.resource)
        eq_('GET', request_span.get_tag('http.method'))
        eq_('500', request_span.get_tag('http.status_code'))
        eq_('/sync_exception/', request_span.get_tag('http.url'))
        eq_(1, request_span.error)
        eq_('Ouch!', request_span.get_tag('error.msg'))
        ok_('Exception: Ouch!' in request_span.get_tag('error.stack'))

    def test_404_handler(self):
        # it should trace 404
        response = self.fetch('/does_not_exist/')
        eq_(404, response.code)

        traces = self.tracer.writer.pop_traces()
        eq_(1, len(traces))
        eq_(1, len(traces[0]))

        request_span = traces[0][0]
        eq_('tornado-web', request_span.service)
        eq_('tornado.request', request_span.name)
        eq_('http', request_span.span_type)
        eq_('tornado.web.ErrorHandler', request_span.resource)
        eq_('GET', request_span.get_tag('http.method'))
        eq_('404', request_span.get_tag('http.status_code'))
        eq_('/does_not_exist/', request_span.get_tag('http.url'))
        eq_(0, request_span.error)

    def test_redirect_handler(self):
        # it should trace the built-in RedirectHandler
        response = self.fetch('/redirect/')
        eq_(200, response.code)

        # we trace two different calls: the RedirectHandler and the SuccessHandler
        traces = self.tracer.writer.pop_traces()
        eq_(2, len(traces))
        eq_(1, len(traces[0]))
        eq_(1, len(traces[1]))

        redirect_span = traces[0][0]
        eq_('tornado-web', redirect_span.service)
        eq_('tornado.request', redirect_span.name)
        eq_('http', redirect_span.span_type)
        eq_('tornado.web.RedirectHandler', redirect_span.resource)
        eq_('GET', redirect_span.get_tag('http.method'))
        eq_('301', redirect_span.get_tag('http.status_code'))
        eq_('/redirect/', redirect_span.get_tag('http.url'))
        eq_(0, redirect_span.error)

        success_span = traces[1][0]
        eq_('tornado-web', success_span.service)
        eq_('tornado.request', success_span.name)
        eq_('http', success_span.span_type)
        eq_('tests.contrib.tornado.web.app.SuccessHandler', success_span.resource)
        eq_('GET', success_span.get_tag('http.method'))
        eq_('200', success_span.get_tag('http.status_code'))
        eq_('/success/', success_span.get_tag('http.url'))
        eq_(0, success_span.error)

    def test_static_handler(self):
        # it should trace the access to static files
        response = self.fetch('/statics/empty.txt')
        eq_(200, response.code)
        eq_('Static file\n', response.body.decode('utf-8'))

        traces = self.tracer.writer.pop_traces()
        eq_(1, len(traces))
        eq_(1, len(traces[0]))

        request_span = traces[0][0]
        eq_('tornado-web', request_span.service)
        eq_('tornado.request', request_span.name)
        eq_('http', request_span.span_type)
        eq_('tornado.web.StaticFileHandler', request_span.resource)
        eq_('GET', request_span.get_tag('http.method'))
        eq_('200', request_span.get_tag('http.status_code'))
        eq_('/statics/empty.txt', request_span.get_tag('http.url'))
        eq_(0, request_span.error)

    def test_propagation(self):
        # it should trace a handler that returns 200 with a propagated context
        headers = {
            'x-datadog-trace-id': '1234',
            'x-datadog-parent-id': '4567',
            'x-datadog-sampling-priority': '2'
        }
        response = self.fetch('/success/', headers=headers)
        eq_(200, response.code)

        traces = self.tracer.writer.pop_traces()
        eq_(1, len(traces))
        eq_(1, len(traces[0]))

        request_span = traces[0][0]

        # simple sanity check on the span
        eq_('tornado.request', request_span.name)
        eq_('200', request_span.get_tag('http.status_code'))
        eq_('/success/', request_span.get_tag('http.url'))
        eq_(0, request_span.error)

        # check propagation
        eq_(1234, request_span.trace_id)
        eq_(4567, request_span.parent_id)
        eq_(2, request_span.get_metric(SAMPLING_PRIORITY_KEY))

    def test_success_handler_ot(self):
        """OpenTracing version of test_success_handler."""
        ot_tracer = init_tracer('tornado_svc', self.tracer, scope_manager=TornadoScopeManager())

        with ot_tracer.start_active_span('tornado_op'):
            response = self.fetch('/success/')
            eq_(200, response.code)

        traces = self.tracer.writer.pop_traces()
        eq_(1, len(traces))
        eq_(2, len(traces[0]))
        # dd_span will start and stop before the ot_span finishes
        ot_span, dd_span = traces[0]

        # confirm the parenting
        eq_(ot_span.parent_id, None)
        eq_(dd_span.parent_id, ot_span.span_id)

        eq_(ot_span.name, 'tornado_op')
        eq_(ot_span.service, 'tornado_svc')

        eq_('tornado-web', dd_span.service)
        eq_('tornado.request', dd_span.name)
        eq_('http', dd_span.span_type)
        eq_('tests.contrib.tornado.web.app.SuccessHandler', dd_span.resource)
        eq_('GET', dd_span.get_tag('http.method'))
        eq_('200', dd_span.get_tag('http.status_code'))
        eq_('/success/', dd_span.get_tag('http.url'))
        eq_(0, dd_span.error)


class TestTornadoWebAnalyticsDefault(TornadoTestCase):
    """
    Ensure that Tornado web handlers generate APM events with default settings
    """
    def test_analytics_global_on_integration_default(self):
        """
        When making a request
            When an integration trace search is not event sample rate is not set and globally trace search is enabled
                We expect the root span to have the appropriate tag
        """
        with self.override_global_config(dict(analytics_enabled=True)):
            # it should trace a handler that returns 200
            response = self.fetch('/success/')
            self.assertEqual(200, response.code)

            self.assert_structure(
                dict(name='tornado.request', metrics={ANALYTICS_SAMPLE_RATE_KEY: 1.0}),
            )

    def test_analytics_global_off_integration_default(self):
        """
        When making a request
            When an integration trace search is not set and sample rate is set and globally trace search is disabled
                We expect the root span to not include tag
        """
        with self.override_global_config(dict(analytics_enabled=False)):
            # it should trace a handler that returns 200
            response = self.fetch('/success/')
            self.assertEqual(200, response.code)

            root = self.get_root_span()
            self.assertIsNone(root.get_metric(ANALYTICS_SAMPLE_RATE_KEY))


class TestTornadoWebAnalyticsOn(TornadoTestCase):
    """
    Ensure that Tornado web handlers generate APM events with default settings
    """
    def get_settings(self):
        # distributed_tracing needs to be disabled manually
        return {
            'datadog_trace': {
                'analytics_enabled': True,
                'analytics_sample_rate': 0.5,
            },
        }

    def test_analytics_global_on_integration_on(self):
        """
        When making a request
            When an integration trace search is enabled and sample rate is set and globally trace search is enabled
                We expect the root span to have the appropriate tag
        """
        with self.override_global_config(dict(analytics_enabled=True)):
            # it should trace a handler that returns 200
            response = self.fetch('/success/')
            self.assertEqual(200, response.code)

            self.assert_structure(
                dict(name='tornado.request', metrics={ANALYTICS_SAMPLE_RATE_KEY: 0.5}),
            )

    def test_analytics_global_off_integration_on(self):
        """
        When making a request
            When an integration trace search is enabled and sample rate is set and globally trace search is disabled
                We expect the root span to have the appropriate tag
        """
        with self.override_global_config(dict(analytics_enabled=False)):
            # it should trace a handler that returns 200
            response = self.fetch('/success/')
            self.assertEqual(200, response.code)

            self.assert_structure(
                dict(name='tornado.request', metrics={ANALYTICS_SAMPLE_RATE_KEY: 0.5}),
            )


class TestTornadoWebAnalyticsNoRate(TornadoTestCase):
    """
    Ensure that Tornado web handlers generate APM events with default settings
    """
    def get_settings(self):
        # distributed_tracing needs to be disabled manually
        return {
            'datadog_trace': {
                'analytics_enabled': True,
            },
        }

    def test_analytics_global_on_integration_on(self):
        """
        When making a request
            When an integration trace search is enabled and sample rate is set and globally trace search is enabled
                We expect the root span to have the appropriate tag
        """
        with self.override_global_config(dict(analytics_enabled=True)):
            # it should trace a handler that returns 200
            response = self.fetch('/success/')
            self.assertEqual(200, response.code)

            self.assert_structure(
                dict(name='tornado.request', metrics={ANALYTICS_SAMPLE_RATE_KEY: 1.0}),
            )


class TestNoPropagationTornadoWeb(TornadoTestCase):
    """
    Ensure that Tornado web handlers are properly traced and are ignoring propagated HTTP headers when disabled.
    """
    def get_settings(self):
        # distributed_tracing needs to be disabled manually
        return {
            'datadog_trace': {
                'distributed_tracing': False,
            },
        }

    def test_no_propagation(self):
        # it should not propagate the HTTP context
        headers = {
            'x-datadog-trace-id': '1234',
            'x-datadog-parent-id': '4567',
            'x-datadog-sampling-priority': '2',
            'x-datadog-origin': 'synthetics',
        }
        response = self.fetch('/success/', headers=headers)
        eq_(200, response.code)

        traces = self.tracer.writer.pop_traces()
        eq_(1, len(traces))
        eq_(1, len(traces[0]))

        request_span = traces[0][0]

        # simple sanity check on the span
        eq_('tornado.request', request_span.name)
        eq_('200', request_span.get_tag('http.status_code'))
        eq_('/success/', request_span.get_tag('http.url'))
        eq_(0, request_span.error)

        # check non-propagation
        assert request_span.trace_id != 1234
        assert request_span.parent_id != 4567
        assert request_span.get_metric(SAMPLING_PRIORITY_KEY) != 2
        assert request_span.get_tag(ORIGIN_KEY) != 'synthetics'


class TestCustomTornadoWeb(TornadoTestCase):
    """
    Ensure that Tornado web handlers are properly traced when using
    a custom default handler.
    """
    def get_settings(self):
        return {
            'default_handler_class': CustomDefaultHandler,
            'default_handler_args': dict(status_code=400),
        }

    def test_custom_default_handler(self):
        # it should trace any call that uses a custom default handler
        response = self.fetch('/custom_handler/')
        eq_(400, response.code)

        traces = self.tracer.writer.pop_traces()
        eq_(1, len(traces))
        eq_(1, len(traces[0]))

        request_span = traces[0][0]
        eq_('tornado-web', request_span.service)
        eq_('tornado.request', request_span.name)
        eq_('http', request_span.span_type)
        eq_('tests.contrib.tornado.web.app.CustomDefaultHandler', request_span.resource)
        eq_('GET', request_span.get_tag('http.method'))
        eq_('400', request_span.get_tag('http.status_code'))
        eq_('/custom_handler/', request_span.get_tag('http.url'))
        eq_(0, request_span.error)
