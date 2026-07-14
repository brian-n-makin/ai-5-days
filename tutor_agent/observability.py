import logging
import os
from typing import Any
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, ConsoleSpanExporter

def setup_telemetry() -> None:
    """Configures application-wide logging and OpenTelemetry tracing."""
    # 1. Logging Setup
    log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logger = logging.getLogger("tutor_agent")
    logger.info("Observability and tracing pipeline initialized.")

    # 2. OpenTelemetry Tracing Setup
    try:
        # Only set provider if one hasn't been set yet
        if not isinstance(trace.get_tracer_provider(), TracerProvider):
            provider = TracerProvider()
            
            # If TRACE_TO_CONSOLE is enabled, print OpenTelemetry spans to stdout
            if os.environ.get("TRACE_TO_CONSOLE") == "true":
                processor = SimpleSpanProcessor(ConsoleSpanExporter())
                provider.add_span_processor(processor)
                
            trace.set_tracer_provider(provider)
            logger.info("OpenTelemetry TracerProvider registered successfully.")
    except Exception as e:
        logger.warning(f"Failed to register OpenTelemetry TracerProvider: {e}")

def get_tracer() -> trace.Tracer:
    """Returns the application tracer instance."""
    return trace.get_tracer("tutor_agent")
