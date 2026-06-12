import unittest

from app.schemas.configuration import ConfigurationCreateRequest
from app.services.configuration_service import ConfigurationService


class FakeConfigurationRepository:
    def __init__(self, items: list[dict]) -> None:
        self.items = [dict(item) for item in items]
        self.replaced_with: list[dict] | None = None
        self.created_payload: dict | None = None

    def list_all(self) -> list[dict]:
        return [dict(item) for item in self.items]

    def get_by_id(self, configuration_id: str) -> dict | None:
        for item in self.items:
            if item["id"] == configuration_id:
                return dict(item)
        return None

    def replace_all(self, configurations: list[dict]) -> None:
        self.replaced_with = [dict(item) for item in configurations]
        self.items = [dict(item) for item in configurations]

    def create(self, configuration: dict) -> dict:
        self.created_payload = dict(configuration)
        self.items.append(dict(configuration))
        return dict(configuration)


class FakeProgramadorAtuacaoService:
    def __init__(self) -> None:
        self.sent_configurations: list[dict] = []

    def send_configuration(self, configuration: dict) -> None:
        self.sent_configurations.append(dict(configuration))


class ConfigurationServiceTests(unittest.TestCase):
    def test_list_configurations_warns_when_none_is_active(self) -> None:
        repository = FakeConfigurationRepository(
            [
                {
                    "id": "cfg-001",
                    "name": "Configuração A",
                    "description": "Padrão",
                    "is_active": False,
                    "created_at": "2026-01-01T10:00:00",
                    "updated_at": "2026-01-01T10:00:00",
                    "parameters": {},
                }
            ]
        )
        service = ConfigurationService(repository, FakeProgramadorAtuacaoService())

        response = service.list_configurations()

        self.assertEqual(response.total, 1)
        self.assertIn("No active configuration selected", response.message)

    def test_get_effective_configuration_uses_oldest_when_none_is_active(self) -> None:
        repository = FakeConfigurationRepository(
            [
                {
                    "id": "cfg-002",
                    "name": "Mais nova",
                    "description": "Nova",
                    "is_active": False,
                    "created_at": "2026-01-02T10:00:00",
                    "updated_at": "2026-01-02T10:00:00",
                    "parameters": {"movement_speed": 1.0},
                },
                {
                    "id": "cfg-001",
                    "name": "Mais antiga",
                    "description": "Antiga",
                    "is_active": False,
                    "created_at": "2026-01-01T10:00:00",
                    "updated_at": "2026-01-01T10:00:00",
                    "parameters": {"movement_speed": 0.5},
                },
            ]
        )
        service = ConfigurationService(repository, FakeProgramadorAtuacaoService())

        response = service.get_effective_configuration()

        self.assertEqual(response.source, "default")
        self.assertEqual(response.configuration.id, "cfg-001")

    def test_set_active_configuration_persists_single_active_item(self) -> None:
        repository = FakeConfigurationRepository(
            [
                {
                    "id": "cfg-001",
                    "name": "A",
                    "description": "Primeira",
                    "is_active": True,
                    "created_at": "2026-01-01T10:00:00",
                    "updated_at": "2026-01-01T10:00:00",
                    "parameters": {},
                },
                {
                    "id": "cfg-002",
                    "name": "B",
                    "description": "Segunda",
                    "is_active": False,
                    "created_at": "2026-01-02T10:00:00",
                    "updated_at": "2026-01-02T10:00:00",
                    "parameters": {},
                },
            ]
        )
        external_service = FakeProgramadorAtuacaoService()
        service = ConfigurationService(repository, external_service)

        response = service.set_active_configuration("cfg-002")

        self.assertEqual(response.configuration.id, "cfg-002")
        self.assertEqual(len(external_service.sent_configurations), 1)
        self.assertIsNotNone(repository.replaced_with)
        active_ids = [item["id"] for item in repository.replaced_with if item["is_active"]]
        self.assertEqual(active_ids, ["cfg-002"])

    def test_create_configuration_generates_next_sequential_id(self) -> None:
        repository = FakeConfigurationRepository(
            [
                {
                    "id": "cfg-002",
                    "name": "B",
                    "description": "Segunda",
                    "is_active": False,
                    "created_at": "2026-01-02T10:00:00",
                    "updated_at": "2026-01-02T10:00:00",
                    "parameters": {},
                },
                {
                    "id": "legacy",
                    "name": "Legada",
                    "description": "Formato antigo",
                    "is_active": False,
                    "created_at": "2026-01-03T10:00:00",
                    "updated_at": "2026-01-03T10:00:00",
                    "parameters": {},
                },
            ]
        )
        service = ConfigurationService(repository, FakeProgramadorAtuacaoService())

        created = service.create_configuration(
            ConfigurationCreateRequest(
                name="Nova configuração",
                description="Descrição",
                parameters={
                    "movement_speed": 0.8,
                    "movement_duration_seconds": 30,
                    "video_capture_enabled": True,
                    "audio_capture_enabled": False,
                },
            )
        )

        self.assertEqual(created.id, "cfg-003")
        self.assertEqual(repository.created_payload["id"], "cfg-003")
