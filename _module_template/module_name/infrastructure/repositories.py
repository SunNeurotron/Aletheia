# Copyright 2025 Alant
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# from ...domain.entities import ExampleEntity # Assuming entities are in domain
# from typing import List, Optional, Protocol
# from uuid import UUID
# import logging

# logger = logging.getLogger(__name__)

# # --- Abstract Repository Port (Interface) ---
# # This would typically be in domain.ports or application.ports
# class ExampleRepositoryPort(Protocol):
#     def save(self, entity: ExampleEntity) -> UUID:
#         ...

#     def get_by_id(self, entity_id: UUID) -> Optional[ExampleEntity]:
#         ...

#     def list_all(self) -> List[ExampleEntity]:
#         ...

# # --- SQLAlchemy Repository Implementation (Example) ---
# # Needs SQLAlchemy models defined (e.g., in a models.py or here)
# # from sqlalchemy.orm import Session
# # from .sqlalchemy_models import ExampleModelDB # Assuming you have a DB model

# class SQLAlchemyExampleRepository: # Implements ExampleRepositoryPort
#     def __init__(self, db_session: Any): # db_session would be SQLAlchemy Session
#         self.db = db_session
#         pass

#     def save(self, entity: ExampleEntity) -> UUID:
#         logger.info(f"SQLAlchemyRepo: Saving entity ID {entity.id}")
#         # db_model = ExampleModelDB.from_domain(entity)
#         # self.db.add(db_model)
#         # self.db.commit()
#         # self.db.refresh(db_model) # If DB generates ID or other fields
#         return entity.id # Placeholder

#     def get_by_id(self, entity_id: UUID) -> Optional[ExampleEntity]:
#         logger.info(f"SQLAlchemyRepo: Getting entity ID {entity_id}")
#         # db_model = self.db.query(ExampleModelDB).filter(ExampleModelDB.id == entity_id).first()
#         # return db_model.to_domain() if db_model else None
#         return None # Placeholder

#     def list_all(self) -> List[ExampleEntity]:
#         logger.info("SQLAlchemyRepo: Listing all entities")
#         # db_models = self.db.query(ExampleModelDB).all()
#         # return [model.to_domain() for model in db_models]
#         return [] # Placeholder

# # --- In-Memory Repository Implementation (Example for testing) ---
# class InMemoryExampleRepository: # Implements ExampleRepositoryPort
#     def __init__(self):
#         self._data: Dict[UUID, ExampleEntity] = {}
#         logger.info("InMemoryExampleRepository initialized.")

#     def save(self, entity: ExampleEntity) -> UUID:
#         logger.info(f"InMemoryRepo: Saving entity ID {entity.id}")
#         self._data[entity.id] = entity
#         return entity.id

#     def get_by_id(self, entity_id: UUID) -> Optional[ExampleEntity]:
#         logger.info(f"InMemoryRepo: Getting entity ID {entity_id}")
#         return self._data.get(entity_id)

#     def list_all(self) -> List[ExampleEntity]:
#         logger.info("InMemoryRepo: Listing all entities")
#         return list(self.data.values())

# print("Placeholder for Infrastructure Repositories")
