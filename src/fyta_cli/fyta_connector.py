"""Connector class to manage access to FYTA API."""

from datetime import datetime
from typing import Any
import pytz

from .fyta_client import Client

PLANT_STATUS = {
    1: "too_low",
    2: "low",
    3: "perfect",
    4: "high",
    5: "too_high",
    }


class FytaConnector(object):
    """Connector class to access FYTA API."""

    def __init__(
        self,
        email: str,
        password: str,
        access_token: str = "",
        expiration: datetime | None = None,
        timezone: pytz.timezone = pytz.utc
    ):

        self.email: str = email
        self.password: str = password
        self.client = Client(email, password, access_token, expiration)
        self.online: bool = False
        self.plant_list: dict[int,str] = {}
        self.plants: dict[int,dict[str,Any]] = {}
        self.access_token: str = access_token
        self.expiration: datetime | None = expiration
        self.timezone = timezone

    async def test_connection(self) -> bool:
        """Test if connection to FYTA API works."""

        return await self.client.test_connection()


    async def login(self) -> dict[str, str | datetime]:
        """Login with credentials to get access token."""

        login = await self.client.login()
        self.access_token = login["access_token"]
        self.expiration = login["expiration"]
        self.online = True

        return login


    async def update_plant_list(self) -> dict[int,str]:
        """Get list of all available plants."""

        self.plant_list = await self.client.get_plants()

        return self.plant_list


    async def update_all_plants(self) -> dict[int,dict[str,Any]]:
        """Get data of all available plants."""

        plants: dict[int,dict[str,Any]] = {}

        plant_list = await self.update_plant_list()

        for plant in plant_list.keys():
            current_plant = await self.update_plant_data(plant)
            if current_plant is not {}:
                plants |= {plant: current_plant}

        self.plants = plants

        return plants

    async def update_plant_data(self, plant_id: int) -> dict[str,Any]:
        """Get data of specific plant."""

        p: dict = await self.client.get_plant_data(plant_id)
        plant_data: dict = p["plant"]

        if plant_data["sensor"] is None:
            return {}

        current_plant: dict[str,Any] = {}
        current_plant |= {"online": True}
        current_plant |= {"battery_status": bool(plant_data["sensor"]["is_battery_low"])}
        current_plant |= {"sw_version": plant_data["sensor"]["version"]}
        current_plant |= {"plant_id": plant_data["id"]}
        current_plant |= {"name": plant_data["nickname"]}
        current_plant |= {"scientific_name": plant_data["scientific_name"]}
        current_plant |= {"status": int(plant_data["status"])}
        current_plant |= {"temperature_status": int(plant_data["measurements"]["temperature"]["status"])}
        current_plant |= {"light_status": int(plant_data["measurements"]["light"]["status"])}
        current_plant |= {"moisture_status": int(plant_data["measurements"]["moisture"]["status"])}
        current_plant |= {"salinity_status": int(plant_data["measurements"]["salinity"]["status"])}
        #current_plant |= {"ph": float(plant_data["measurements"]["ph"]["values"]["current"])}
        current_plant |= {"temperature": float(plant_data["measurements"]["temperature"]["values"]["current"])}
        current_plant |= {"light": float(plant_data["measurements"]["light"]["values"]["current"])}
        current_plant |= {"moisture": float(plant_data["measurements"]["moisture"]["values"]["current"])}
        current_plant |= {"salinity": float(plant_data["measurements"]["salinity"]["values"]["current"])}
        current_plant |= {"battery_level": float(plant_data["measurements"]["battery"])}
        current_plant |= {"last_updated": self.timezone.localize(datetime.fromisoformat(plant_data["sensor"]["received_data_at"]))}

        return current_plant

    @property
    def fyta_id(self) -> str:
        """ID for FYTA object"""
        return self.email

    @property
    def data(self) -> dict:
        """ID for FYTA object"""
        return self.plants