import unittest
import urllib.error

from novel_studio.utils.retry import retry_stream_with_backoff


class TestRetry(unittest.TestCase):
    def test_stream_retries_retryable_network_error(self):
        calls = {'n': 0}

        def source():
            calls['n'] += 1
            if calls['n'] == 1:
                raise ConnectionError('temporary')
            yield 'ok'

        wrapped = retry_stream_with_backoff(
            max_retries=1,
            base_delay=0,
            max_delay=0,
            retryable_exceptions=(ConnectionError,),
        )(source)
        self.assertEqual(list(wrapped()), ['ok'])
        self.assertEqual(calls['n'], 2)

    def test_stream_does_not_retry_http_client_error(self):
        calls = {'n': 0}

        def source():
            calls['n'] += 1
            raise urllib.error.HTTPError('x', 400, 'bad request', {}, None)
            yield  # pragma: no cover

        wrapped = retry_stream_with_backoff(
            max_retries=2,
            base_delay=0,
            max_delay=0,
            retryable_exceptions=(urllib.error.HTTPError,),
        )(source)
        with self.assertRaises(urllib.error.HTTPError):
            list(wrapped())
        self.assertEqual(calls['n'], 1)


if __name__ == '__main__':
    unittest.main()
