from typing import List, Dict, Any, Optional, Protocol # Added Protocol
from datetime import datetime
import hashlib
import asyncio # For AlertManager sending alerts

from prometheus_client import Counter, Histogram, Gauge
# OpenTelemetry imports - ensure these are installed
from opentelemetry import trace
# from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter # Full import if used
# from opentelemetry.sdk.trace import TracerProvider
# from opentelemetry.sdk.trace.export import BatchSpanProcessor

# For EmailAlertChannel (standard library)
import smtplib
from email.mime.text import MIMEText


class CubeMonitoring:
    """Sistema de monitoreo completo para el cubo (Prometheus & OpenTelemetry)."""

    def __init__(self, otlp_exporter_endpoint: Optional[str] = None): # e.g., "http://localhost:4317"
        # Prometheus Metrics
        self.rotation_counter = Counter(
            'mdu_cube_rotations_total', # Added mdu_ prefix
            'Total number of MDU cube rotations',
            ['face', 'degrees'] # Labels
        )

        self.analysis_duration_seconds = Histogram( # Renamed from analysis_duration
            'mdu_analysis_duration_seconds',
            'Duration of MDU analysis operations',
            ['level', 'strategy'] # Labels
        )

        self.active_analyses_gauge = Gauge( # Renamed from active_analyses
            'mdu_active_analyses',
            'Number of currently active MDU analyses'
        )

        # OpenTelemetry Tracing Setup (Basic)
        self.tracer = trace.get_tracer("mdu_cube_system.tracer") # Get a tracer instance

        if otlp_exporter_endpoint:
            try:
                from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
                from opentelemetry.sdk.trace import TracerProvider
                from opentelemetry.sdk.trace.export import BatchSpanProcessor

                provider = TracerProvider()
                processor = BatchSpanProcessor(OTLPSpanExporter(endpoint=otlp_exporter_endpoint, insecure=True))
                provider.add_span_processor(processor)
                trace.set_tracer_provider(provider)
                # print(f"CubeMonitoring: OpenTelemetry configured with OTLP exporter to {otlp_exporter_endpoint}.")
            except ImportError:
                print("CubeMonitoring: OpenTelemetry libraries not fully installed. OTLP export disabled.")
            except Exception as e:
                print(f"CubeMonitoring: Failed to initialize OpenTelemetry OTLP exporter: {e}")
        # else:
            # print("CubeMonitoring: OTLP exporter endpoint not provided. OpenTelemetry tracing might be limited to default (noop).")


    def track_rotation(self, face: str, degrees: int):
        """Rastrea rotaciones del cubo."""
        self.rotation_counter.labels(face=face, degrees=str(degrees)).inc()

    def track_analysis_duration(self, level: str, strategy: str): # Renamed from track_analysis
        """Context manager para rastrear la duración de una operación de análisis."""
        return self.analysis_duration_seconds.labels(level=level, strategy=strategy).time()

    def increment_active_analyses(self): # New method
        self.active_analyses_gauge.inc()

    def decrement_active_analyses(self): # New method
        self.active_analyses_gauge.dec()

    # Example of using the tracer (could be a decorator or explicit calls)
    def create_span(self, span_name: str) -> Any: # Returns a Telemetry Span
        """Creates a new OpenTelemetry span. Use in a 'with' statement."""
        return self.tracer.start_as_current_span(span_name)


# --- Alerting System Components (from mdu_cube_system.py Section 11.2) ---
# Dataclass for Alert structure
from dataclasses import dataclass, field # field was missing

@dataclass
class Alert:
    """Representa una alerta del sistema."""
    level: str  # e.g., "INFO", "WARNING", "ERROR", "CRITICAL"
    message: str
    component: str # Componente del sistema que origina la alerta
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    id: str = field(init=False) # Generado automáticamente

    def __post_init__(self):
        # Generar ID único para la alerta
        raw_id_str = f"{self.level}-{self.component}-{self.message[:50]}-{self.timestamp.isoformat()}"
        self.id = hashlib.sha256(raw_id_str.encode()).hexdigest()[:16]

class IAlertChannel(Protocol):
    """Interfaz para canales de notificación de alertas."""
    async def send_alert(self, alert: Alert) -> bool:
        """Envía una alerta a través de este canal."""
        ...

class EmailAlertChannel(IAlertChannel):
    """Implementación de canal de alertas por correo electrónico."""
    def __init__(self, smtp_server: str, smtp_port: int, smtp_user: Optional[str],
                 smtp_password: Optional[str], sender_email: str, recipient_emails: List[str], use_tls: bool = True):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.sender_email = sender_email
        self.recipient_emails = recipient_emails
        self.use_tls = use_tls

    def _format_alert_email(self, alert: Alert) -> MIMEText:
        subject = f"[{alert.level.upper()}] MDU System Alert: {alert.component}"
        body = f"""
        MDU System Alert Notification
        -----------------------------
        ID:         {alert.id}
        Timestamp:  {alert.timestamp.isoformat()}
        Level:      {alert.level.upper()}
        Component:  {alert.component}
        Message:    {alert.message}
        -----------------------------
        Metadata:
        {json.dumps(alert.metadata, indent=2, default=str)}
        """ # Added json.dumps for metadata and default=str for non-serializable
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = self.sender_email
        msg['To'] = ', '.join(self.recipient_emails)
        return msg

    async def send_alert(self, alert: Alert) -> bool:
        """Envía la alerta por correo electrónico."""
        msg = self._format_alert_email(alert)
        try:
            # SMTP operations are typically synchronous.
            # To make this truly async, would need `aiosmtplib` or run in executor.
            # For now, using synchronous smtplib for simplicity.
            # Consider this a blocking call if used in a heavily async environment.
            # This could be wrapped with `await asyncio.to_thread(self._send_sync, msg)` in Python 3.9+

            # Synchronous sending part
            def _send_sync():
                with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=10) as server: # Added timeout
                    if self.use_tls:
                        server.starttls()
                    if self.smtp_user and self.smtp_password:
                        server.login(self.smtp_user, self.smtp_password)
                    server.send_message(msg)
                # print(f"EmailAlertChannel: Alert '{alert.id}' sent to {self.recipient_emails}.")
                return True

            # If in an async context, run the sync code in a thread
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, _send_sync)
            return True

        except Exception as e:
            print(f"EmailAlertChannel: Failed to send email alert '{alert.id}': {e}")
            return False

class AlertRule:
    """Define una regla para generar alertas basadas en métricas."""
    def __init__(self, name: str, condition_callable: Callable[[Dict[str, Any]], bool], # Renamed condition_func
                 component_name: str, # Renamed component
                 alert_level: str = "WARNING"): # Renamed level
        self.name = name
        self.condition = condition_callable
        self.component = component_name
        self.level = alert_level

    def should_alert(self, metrics_snapshot: Dict[str, Any]) -> bool: # Renamed metrics
        """Evalúa si la condición de alerta se cumple con las métricas dadas."""
        try:
            return self.condition(metrics_snapshot)
        except Exception as e:
            # print(f"AlertRule '{self.name}': Error evaluating condition: {e}")
            return False # Fail safe: don't alert if condition check errors

    def create_alert(self, metrics_snapshot: Dict[str, Any]) -> Alert: # Renamed metrics
        """Crea un objeto Alert basado en esta regla y las métricas actuales."""
        return Alert(
            level=self.level,
            message=f"Alert rule '{self.name}' triggered for component '{self.component}'.",
            component=self.component,
            metadata={"triggering_metrics": metrics_snapshot, "rule_name": self.name}
        )

class AlertManager:
    """Gestor central para procesar reglas de alerta y enviar notificaciones."""
    def __init__(self):
        self.alert_channels: List[IAlertChannel] = [] # Renamed channels
        self.alert_history: List[Alert] = []
        self.alert_rules_list: List[AlertRule] = [] # Renamed alert_rules

    def add_channel(self, channel: IAlertChannel):
        self.alert_channels.append(channel)

    def add_rule(self, rule: AlertRule):
        self.alert_rules_list.append(rule)

    async def check_and_dispatch_alerts(self, current_metrics: Dict[str, Any]): # Renamed check_and_alert, metrics
        """Verifica todas las reglas contra las métricas actuales y envía alertas si se activan."""
        alert_dispatch_tasks = []
        for rule in self.alert_rules_list:
            if rule.should_alert(current_metrics):
                alert_instance = rule.create_alert(current_metrics)
                alert_dispatch_tasks.append(self._send_alert_to_all_channels(alert_instance)) # Renamed method

        if alert_dispatch_tasks:
            await asyncio.gather(*alert_dispatch_tasks)

    async def _send_alert_to_all_channels(self, alert: Alert) -> bool: # Renamed send_alert
        """Envía una alerta específica a todos los canales configurados."""
        if not any(isinstance(c, IAlertChannel) for c in self.alert_channels): # Ensure channels list is not empty
             # print(f"AlertManager: No alert channels configured. Alert '{alert.id}' not sent.")
             return False

        self.alert_history.append(alert)
        if len(self.alert_history) > 200: # Increased history size slightly
            self.alert_history = self.alert_history[-200:]

        send_results = await asyncio.gather(
            *(channel.send_alert(alert) for channel in self.alert_channels),
            return_exceptions=True # Capture exceptions from send_alert calls
        )

        successful_sends = [res for res in send_results if isinstance(res, bool) and res]
        failed_sends = [err for err in send_results if isinstance(err, Exception)]

        # if failed_sends:
            # print(f"AlertManager: Some errors occurred sending alert '{alert.id}': {failed_sends}")

        return bool(successful_sends) # True if at least one channel succeeded
