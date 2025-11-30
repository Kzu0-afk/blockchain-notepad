"""
Utility functions for blockchain operations.
"""

import time
import logging
import hashlib
from functools import wraps
from django.core.cache import cache
from django.core.cache.backends.locmem import LocMemCache
from django.conf import settings
from blockfrost import ApiError

logger = logging.getLogger('blockchain')

# Get the blockfrost-specific cache
try:
    blockfrost_cache = LocMemCache('blockfrost-api-cache', {})
except:
    # Fallback to default cache if blockfrost cache fails
    blockfrost_cache = cache


def retry_on_failure(max_retries=3, delay=1, backoff=2, exceptions=(ApiError, Exception)):
    """
    Decorator to retry functions on specific exceptions.

    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Backoff multiplier for delay
        exceptions: Tuple of exceptions to catch and retry on
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt == max_retries:
                        # Final attempt failed
                        logger.error(f'Function {func.__name__} failed after {max_retries} retries: {str(e)}')
                        raise e

                    # Log retry attempt
                    logger.warning(f'Function {func.__name__} failed (attempt {attempt + 1}/{max_retries + 1}): {str(e)}. Retrying in {current_delay}s...')

                    # Wait before retrying
                    time.sleep(current_delay)
                    current_delay *= backoff

            # This should never be reached, but just in case
            raise last_exception

        return wrapper
    return decorator


class CircuitBreaker:
    """
    Simple circuit breaker implementation for API calls.
    """
    def __init__(self, failure_threshold=5, recovery_timeout=60, cache_key_prefix='circuit_breaker'):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.cache_key_prefix = cache_key_prefix

    def _get_cache_key(self, service_name):
        return f'{self.cache_key_prefix}:{service_name}'

    def is_open(self, service_name):
        """
        Check if circuit breaker is open (blocking calls).
        """
        cache_key = self._get_cache_key(service_name)
        failure_data = cache.get(cache_key)

        if not failure_data:
            return False

        failure_count, last_failure_time = failure_data

        # Check if we're still in recovery timeout
        if failure_count >= self.failure_threshold:
            if time.time() - last_failure_time < self.recovery_timeout:
                return True  # Circuit is open
            else:
                # Recovery timeout passed, reset circuit
                cache.delete(cache_key)
                return False

        return False

    def record_success(self, service_name):
        """
        Record a successful call (resets failure count).
        """
        cache_key = self._get_cache_key(service_name)
        cache.delete(cache_key)  # Reset on success

    def record_failure(self, service_name):
        """
        Record a failed call.
        """
        cache_key = self._get_cache_key(service_name)
        failure_data = cache.get(cache_key)

        if failure_data:
            failure_count, last_failure_time = failure_data
            failure_count += 1
        else:
            failure_count = 1

        last_failure_time = time.time()
        cache.set(cache_key, (failure_count, last_failure_time), timeout=self.recovery_timeout * 2)


# Global circuit breaker instance
blockfrost_circuit_breaker = CircuitBreaker(
    failure_threshold=5,
    recovery_timeout=60,  # 1 minute recovery
    cache_key_prefix='blockfrost_circuit'
)


def with_circuit_breaker(service_name='blockfrost'):
    """
    Decorator to apply circuit breaker pattern to functions.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if blockfrost_circuit_breaker.is_open(service_name):
                raise ApiError("Circuit breaker is open - service temporarily unavailable", status_code=503)

            try:
                result = func(*args, **kwargs)
                blockfrost_circuit_breaker.record_success(service_name)
                return result
            except Exception as e:
                blockfrost_circuit_breaker.record_failure(service_name)
                raise e

        return wrapper
    return decorator


def cached_blockfrost_call(timeout=None, cache_key_prefix='blockfrost'):
    """
    Decorator to cache Blockfrost API calls using Django's cache framework.

    Args:
        timeout: Cache timeout in seconds (uses settings default if None)
        cache_key_prefix: Prefix for cache keys
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            key_parts = [cache_key_prefix, func.__name__]
            key_parts.extend(str(arg) for arg in args if arg is not None)
            key_parts.extend(f"{k}:{v}" for k, v in kwargs.items() if v is not None)

            cache_key = hashlib.md5(':'.join(key_parts).encode()).hexdigest()

            # Try to get from cache first
            cached_result = blockfrost_cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {func.__name__}: {cache_key}")
                return cached_result

            # Cache miss - call the function
            logger.debug(f"Cache miss for {func.__name__}: {cache_key}")
            result = func(*args, **kwargs)

            # Cache the result
            actual_timeout = timeout or getattr(settings, 'BLOCKFROST_CACHE_TIMEOUT', 300)
            blockfrost_cache.set(cache_key, result, actual_timeout)

            return result

        return wrapper
    return decorator


@retry_on_failure(max_retries=2, delay=0.5, exceptions=(ApiError,))
@with_circuit_breaker()
@cached_blockfrost_call()
def safe_blockfrost_call(func, *args, **kwargs):
    """
    Wrapper function for safe Blockfrost API calls with retry, circuit breaker, and caching.

    Usage:
        result = safe_blockfrost_call(api.transaction, tx_hash)
    """
    return func(*args, **kwargs)


@retry_on_failure(max_retries=2, delay=0.5, exceptions=(ApiError,))
@with_circuit_breaker()
@cached_blockfrost_call(timeout=60)  # Balance data changes more frequently
def safe_blockfrost_balance_call(func, *args, **kwargs):
    """
    Wrapper function for balance-related Blockfrost API calls with shorter cache timeout.

    Usage:
        result = safe_blockfrost_balance_call(api.address_utxos, address)
    """
    return func(*args, **kwargs)
