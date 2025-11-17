"""Unit tests for UUID to ID mapping in entity resolution."""

from abzu.er.uuid import UUIDMapper


class TestUUIDMapper:
    """Test the UUIDMapper class for correct ID assignment and reverse mapping."""

    def test_mapper_initialization(self) -> None:
        """Test that mapper initializes with next_id=1."""
        mapper = UUIDMapper()
        assert mapper.next_id == 1
        assert len(mapper.uuid_to_int) == 0
        assert len(mapper.int_to_uuid) == 0

    def test_add_uuid_sequential(self) -> None:
        """Test that UUIDs are assigned sequential IDs starting from 1."""
        mapper = UUIDMapper()

        uuid1 = "637612a2-fbbe-4be0-9373-7c207bde193c"
        uuid2 = "7f1dc05a-f45c-4229-8f3e-dbba8b3e25e7"
        uuid3 = "f1c6ddff-864f-4b32-9514-7ab8f0e04ae2"

        id1 = mapper.add_uuid(uuid1)
        id2 = mapper.add_uuid(uuid2)
        id3 = mapper.add_uuid(uuid3)

        assert id1 == 1
        assert id2 == 2
        assert id3 == 3

    def test_add_uuid_idempotent(self) -> None:
        """Test that adding same UUID returns same ID."""
        mapper = UUIDMapper()

        uuid = "637612a2-fbbe-4be0-9373-7c207bde193c"

        id1 = mapper.add_uuid(uuid)
        id2 = mapper.add_uuid(uuid)
        id3 = mapper.add_uuid(uuid)

        assert id1 == id2 == id3 == 1

    def test_get_uuid_valid(self) -> None:
        """Test retrieving UUID by ID."""
        mapper = UUIDMapper()

        uuid1 = "637612a2-fbbe-4be0-9373-7c207bde193c"
        uuid2 = "7f1dc05a-f45c-4229-8f3e-dbba8b3e25e7"

        id1 = mapper.add_uuid(uuid1)
        id2 = mapper.add_uuid(uuid2)

        assert mapper.get_uuid(id1) == uuid1
        assert mapper.get_uuid(id2) == uuid2

    def test_get_uuid_invalid(self) -> None:
        """Test retrieving non-existent ID returns None."""
        mapper = UUIDMapper()

        uuid = "637612a2-fbbe-4be0-9373-7c207bde193c"
        mapper.add_uuid(uuid)

        assert mapper.get_uuid(999) is None

    def test_map_ids_to_uuids(self) -> None:
        """Test mapping list of IDs to UUIDs."""
        mapper = UUIDMapper()

        uuid1 = "637612a2-fbbe-4be0-9373-7c207bde193c"
        uuid2 = "7f1dc05a-f45c-4229-8f3e-dbba8b3e25e7"
        uuid3 = "f1c6ddff-864f-4b32-9514-7ab8f0e04ae2"

        id1 = mapper.add_uuid(uuid1)
        id2 = mapper.add_uuid(uuid2)
        id3 = mapper.add_uuid(uuid3)

        # Map back
        uuids = mapper.map_ids_to_uuids([id1, id2, id3])

        assert uuids == [uuid1, uuid2, uuid3]

    def test_map_ids_to_uuids_none(self) -> None:
        """Test mapping None returns None."""
        mapper = UUIDMapper()
        assert mapper.map_ids_to_uuids(None) is None

    def test_map_ids_to_uuids_empty(self) -> None:
        """Test mapping empty list returns None."""
        mapper = UUIDMapper()
        assert mapper.map_ids_to_uuids([]) is None

    def test_map_ids_to_uuids_invalid_id(self) -> None:
        """Test mapping with invalid ID skips it."""
        mapper = UUIDMapper()

        uuid1 = "637612a2-fbbe-4be0-9373-7c207bde193c"
        id1 = mapper.add_uuid(uuid1)

        # Try to map including invalid ID
        uuids = mapper.map_ids_to_uuids([id1, 999])

        # Should only return the valid UUID
        assert uuids == [uuid1]

    def test_map_uuids_to_ids(self) -> None:
        """Test mapping list of UUIDs to IDs."""
        mapper = UUIDMapper()

        uuid1 = "637612a2-fbbe-4be0-9373-7c207bde193c"
        uuid2 = "7f1dc05a-f45c-4229-8f3e-dbba8b3e25e7"

        # First add should create mappings
        ids = mapper.map_uuids_to_ids([uuid1, uuid2])

        assert ids == [1, 2]
        assert mapper.get_uuid(1) == uuid1
        assert mapper.get_uuid(2) == uuid2

    def test_map_uuids_to_ids_none(self) -> None:
        """Test mapping None returns None."""
        mapper = UUIDMapper()
        assert mapper.map_uuids_to_ids(None) is None

    def test_map_uuids_to_ids_empty(self) -> None:
        """Test mapping empty list returns None."""
        mapper = UUIDMapper()
        assert mapper.map_uuids_to_ids([]) is None

    def test_round_trip_mapping(self) -> None:
        """Test UUID -> ID -> UUID round trip preserves values."""
        mapper = UUIDMapper()

        original_uuids = [
            "637612a2-fbbe-4be0-9373-7c207bde193c",
            "7f1dc05a-f45c-4229-8f3e-dbba8b3e25e7",
            "f1c6ddff-864f-4b32-9514-7ab8f0e04ae2",
        ]

        # UUID -> ID
        ids = mapper.map_uuids_to_ids(original_uuids)

        # ID -> UUID
        recovered_uuids = mapper.map_ids_to_uuids(ids)

        assert recovered_uuids == original_uuids
