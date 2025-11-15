from opentelemetry import metrics, trace
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider

resource = Resource.create({"service.name": "piazzati-backend", "service.version": "1.0.0"})
prometheus_reader = PrometheusMetricReader(disable_target_info=True)
meter_provider = MeterProvider(metric_readers=[prometheus_reader], resource=resource)
metrics.set_meter_provider(meter_provider)
tracer_provider = TracerProvider()
trace.set_tracer_provider(tracer_provider)
meter = metrics.get_meter(__name__)
tracer = trace.get_tracer(__name__)

request_count = meter.create_counter(
    "piazzati_custom_requests_total",
    description="Total number of requests tracked by custom counter",
    unit="1",
)
request_duration = meter.create_histogram(
    "piazzati_custom_request_duration_seconds",
    description="Request duration in seconds tracked by custom histogram",
    unit="s",
)
database_operations = meter.create_counter(
    "piazzati_custom_database_operations_total",
    description="Total number of database operations tracked by custom counter",
    unit="1",
)
active_users = meter.create_up_down_counter(
    "piazzati_custom_active_users",
    description="Number of active users tracked by custom counter",
    unit="1",
)
