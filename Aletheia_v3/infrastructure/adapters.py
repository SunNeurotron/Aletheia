from typing import List, Dict, Optional, Any
from abc import ABC, abstractmethod
import json
from datetime import datetime
import asyncio # For KafkaAdapter sleep, and general async
import aiohttp # For GraphQLAdapter

# Application port (though ExternalServiceAdapter is defined here, it acts as one)
# from ..application.ports import ... # If there were a generic IExternalServicePort

class ExternalServiceAdapter(ABC):
    """Adaptador base para servicios externos."""
    @abstractmethod
    async def connect(self) -> bool:
        """Establece conexión con el servicio."""
        pass

    @abstractmethod
    async def send_data(self, data_payload: Dict[str, Any], target_identifier: Optional[str] = None) -> Dict[str, Any]:
        """Envía datos al servicio. target_identifier could be a topic, table, query name, etc."""
        pass

    @abstractmethod
    async def receive_data(self, source_identifier: Optional[str] = None, query_params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Recibe datos del servicio. source_identifier could be topic, table, etc. query_params for filtering."""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Cierra la conexión con el servicio."""
        pass


class KafkaAdapter(ExternalServiceAdapter):
    """Adaptador para Apache Kafka."""

    def __init__(self, bootstrap_servers: List[str]):
        self.bootstrap_servers = bootstrap_servers
        self.producer: Optional[Any] = None # Using Any for AIOKafkaProducer to avoid direct import here if problematic
        self.consumer: Optional[Any] = None # Using Any for AIOKafkaConsumer
        self.loop = asyncio.get_event_loop() # Get event loop during init
        self._kafka_producer_class: Optional[type] = None
        self._kafka_consumer_class: Optional[type] = None

    async def _lazy_load_kafka_libs(self):
        if self._kafka_producer_class is None or self._kafka_consumer_class is None:
            try:
                from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
                self._kafka_producer_class = AIOKafkaProducer
                self._kafka_consumer_class = AIOKafkaConsumer
            except ImportError:
                print("KafkaAdapter Error: aiokafka library is not installed. Kafka features will not work.")
                # Set them to a type that will prevent further operations or raise clearly
                class KafkaNotAvailable:
                    async def start(self): pass
                    async def stop(self): pass
                    async def send_and_wait(self, *args, **kwargs): raise RuntimeError("aiokafka not available")
                    async def getone(self, *args, **kwargs): raise RuntimeError("aiokafka not available")
                    def subscription(self): return set()

                self._kafka_producer_class = KafkaNotAvailable # type: ignore
                self._kafka_consumer_class = KafkaNotAvailable # type: ignore


    async def connect(self) -> bool:
        """Conecta con Kafka (specifically, starts the producer)."""
        await self._lazy_load_kafka_libs()
        if self._kafka_producer_class is None or self._kafka_producer_class.__name__ == 'KafkaNotAvailable':
            return False
        try:
            self.producer = self._kafka_producer_class(
                loop=self.loop,
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            await self.producer.start()
            # print(f"KafkaAdapter: Producer connected to {self.bootstrap_servers}.")
            return True
        except Exception as e:
            print(f"KafkaAdapter: Producer connect failed for {self.bootstrap_servers}: {e}")
            self.producer = None
            return False

    async def send_data(self, data_payload: Dict[str, Any], target_identifier: Optional[str] = None) -> Dict[str, Any]:
        """Envía evento a Kafka. target_identifier is the topic."""
        if not self.producer:
            return {'status': 'error', 'message': 'KafkaProducer not connected or aiokafka not available.'}
        if not target_identifier: # Topic must be provided
            return {'status': 'error', 'message': 'Kafka topic (target_identifier) is required for send_data.'}

        try:
            await self.producer.send_and_wait(target_identifier, value=data_payload)
            return {'status': 'sent_to_kafka', 'topic': target_identifier, 'timestamp': datetime.now().isoformat()}
        except Exception as e:
            return {'status': 'kafka_send_error', 'message': str(e)}

    async def receive_data(self, source_identifier: Optional[str] = None, query_params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Recibe un mensaje de un topic de Kafka. source_identifier is the topic."""
        await self._lazy_load_kafka_libs()
        if self._kafka_consumer_class is None or self._kafka_consumer_class.__name__ == 'KafkaNotAvailable':
            return None
        if not source_identifier:
            # print("KafkaAdapter: Topic (source_identifier) missing for receive_data.")
            return None

        # Consumer setup can be complex (group_id, offsets). This is simplified.
        # For getone, a unique group_id is often used if not managing offsets carefully.
        consumer_group_id = query_params.get("group_id", f"mdu_kafka_adapter_consumer_{source_identifier}_{random.randint(1,100000)}")
        consumer_timeout = query_params.get("timeout_ms", 2000) # Default 2s timeout for getone

        try:
            # Create consumer on demand if not already configured for this topic/group
            # This is not ideal for high-performance scenarios but simpler for an adapter.
            if not self.consumer or self.consumer.subscription() != {source_identifier}: # type: ignore
                if self.consumer: await self.consumer.stop() # type: ignore

                self.consumer = self._kafka_consumer_class( # type: ignore
                    source_identifier,
                    loop=self.loop,
                    bootstrap_servers=self.bootstrap_servers,
                    group_id=consumer_group_id,
                    value_deserializer=lambda v_bytes: json.loads(v_bytes.decode('utf-8')),
                    auto_offset_reset=query_params.get("auto_offset_reset", 'earliest'),
                    consumer_timeout_ms=consumer_timeout
                )
                await self.consumer.start() # type: ignore

            msg = await self.consumer.getone() # type: ignore # Gets one message, blocks with timeout
            return msg.value if msg else None
        except asyncio.TimeoutError:
            # print(f"KafkaAdapter: Timeout receiving message from topic '{source_identifier}'.")
            return None
        except Exception as e:
            print(f"KafkaAdapter: receive_data error from topic '{source_identifier}': {e}")
            if self.consumer :
                await self.consumer.stop() # type: ignore
                self.consumer = None
            return None

    async def close(self) -> None:
        """Cierra conexiones de productor y consumidor."""
        if self.producer:
            try: await self.producer.stop()
            except Exception as e_prod: print(f"KafkaAdapter: Producer stop error: {e_prod}")
            self.producer = None
        if self.consumer:
            try: await self.consumer.stop()
            except Exception as e_cons: print(f"KafkaAdapter: Consumer stop error: {e_cons}")
            self.consumer = None
        # print("KafkaAdapter: Closed connections.")


class GraphQLAdapter(ExternalServiceAdapter):
    """Adaptador para APIs GraphQL."""
    def __init__(self, endpoint_url: str, request_headers: Optional[Dict[str, str]] = None):
        self.endpoint = endpoint_url
        self.headers = request_headers or {}
        self.session: Optional[aiohttp.ClientSession] = None

    async def connect(self) -> bool:
        """Establece sesión HTTP."""
        try:
            # Add default content type if not provided, as GraphQL usually expects JSON
            if 'Content-Type' not in self.headers:
                self.headers['Content-Type'] = 'application/json'

            self.session = aiohttp.ClientSession(headers=self.headers)
            # Optional: Test connection with a simple introspection query (can be verbose)
            # async with self.session.post(self.endpoint, json={'query': '{ __typename }'}) as resp:
            #     if resp.status == 200: return True
            # return False
            # print(f"GraphQLAdapter: Session created for {self.endpoint}.")
            return True
        except Exception as e:
            print(f"GraphQLAdapter: connect failed for {self.endpoint}: {e}")
            if self.session and not self.session.closed: await self.session.close()
            self.session = None
            return False

    async def send_data(self, data_payload: Dict[str, Any], target_identifier: Optional[str] = None) -> Dict[str, Any]:
        """Ejecuta query/mutación GraphQL. data_payload should contain 'query' and optionally 'variables'."""
        if not self.session or self.session.closed:
            return {'error': 'GraphQL session not connected or closed.'}

        if 'query' not in data_payload:
            return {'error': 'GraphQL query missing in data_payload.'}

        try:
            async with self.session.post(self.endpoint, json=data_payload) as response:
                if 'application/json' in response.headers.get('Content-Type','').lower():
                    return await response.json()
                else:
                    text_response = await response.text()
                    return {'error': f'Non-JSON response from GraphQL server (status {response.status})',
                            'details': text_response[:500]} # Truncate long HTML errors
        except aiohttp.ClientConnectionError as e_conn: # More specific exception
             return {'error': f'GraphQL connection error to {self.endpoint}: {e_conn}'}
        except Exception as e_gen:
            return {'error': f'GraphQL send_data unexpected error: {str(e_gen)}'}

    async def receive_data(self, source_identifier: Optional[str] = None, query_params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Ejecuta una query GraphQL. source_identifier is the query string, query_params are variables."""
        if not source_identifier:
            # print("GraphQLAdapter: Query string (source_identifier) missing for receive_data.")
            return None

        graphql_payload: Dict[str, Any] = {'query': source_identifier}
        if query_params:
            graphql_payload['variables'] = query_params

        response_dict = await self.send_data(graphql_payload)
        return response_dict if 'error' not in response_dict else None

    async def close(self) -> None:
        """Cierra la sesión aiohttp."""
        if self.session and not self.session.closed:
            await self.session.close()
        # print(f"GraphQLAdapter: Closed session for {self.endpoint}.")
        self.session = None
