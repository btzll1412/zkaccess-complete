"""Services for ZKAccess Complete Control System."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall
import homeassistant.helpers.config_validation as cv

from .const import (
    DOMAIN,
    SERVICE_ADD_USER,
    SERVICE_UPDATE_USER,
    SERVICE_DELETE_USER,
    SERVICE_LOCK_ALL_DOORS,
    SERVICE_UNLOCK_ALL_DOORS,
    ATTR_USER_NAME,
    ATTR_CARD_NUMBER,
    ATTR_PIN_CODE,
    ATTR_VERIFY_MODE,
    ATTR_GROUPS,
    ATTR_START_DATE,
    ATTR_END_DATE,
)

_LOGGER = logging.getLogger(__name__)

# Service schemas
SERVICE_ADD_USER_SCHEMA = vol.Schema({
    vol.Required(ATTR_USER_NAME): cv.string,
    vol.Optional(ATTR_CARD_NUMBER): cv.string,
    vol.Optional(ATTR_PIN_CODE): cv.string,
    vol.Optional(ATTR_VERIFY_MODE, default="card_only"): vol.In([
        "card_only", "pin_only", "card_or_pin", "card_and_pin"
    ]),
    vol.Optional(ATTR_GROUPS, default=[]): vol.All(cv.ensure_list, [cv.string]),
    vol.Optional(ATTR_START_DATE): cv.string,
    vol.Optional(ATTR_END_DATE): cv.string,
})

SERVICE_UPDATE_USER_SCHEMA = vol.Schema({
    vol.Required("user_id"): cv.positive_int,
    vol.Optional(ATTR_USER_NAME): cv.string,
    vol.Optional(ATTR_CARD_NUMBER): cv.string,
    vol.Optional(ATTR_PIN_CODE): cv.string,
    vol.Optional(ATTR_VERIFY_MODE): vol.In([
        "card_only", "pin_only", "card_or_pin", "card_and_pin"
    ]),
    vol.Optional(ATTR_GROUPS): vol.All(cv.ensure_list, [cv.string]),
    vol.Optional(ATTR_START_DATE): cv.string,
    vol.Optional(ATTR_END_DATE): cv.string,
})

SERVICE_DELETE_USER_SCHEMA = vol.Schema({
    vol.Required("user_id"): cv.positive_int,
})

SERVICE_LOCK_ALL_SCHEMA = vol.Schema({
    vol.Optional("except_doors", default=[]): vol.All(cv.ensure_list, [cv.positive_int]),
})

SERVICE_UNLOCK_ALL_SCHEMA = vol.Schema({
    vol.Optional("only_doors", default=[]): vol.All(cv.ensure_list, [cv.positive_int]),
    vol.Optional("duration", default=5): cv.positive_int,
})


async def async_setup_services(hass: HomeAssistant) -> None:
    """Set up services for ZKAccess."""
    
    async def handle_add_user(call: ServiceCall) -> None:
        """Handle add user service call."""
        _LOGGER.info("Adding user: %s", call.data.get(ATTR_USER_NAME))
        
        # Get storage helper
        store = hass.data[DOMAIN].get("store")
        if not store:
            _LOGGER.error("Storage not initialized")
            return
        
        # Create user record
        user_data = {
            "name": call.data.get(ATTR_USER_NAME),
            "card_number": call.data.get(ATTR_CARD_NUMBER),
            "pin_code": call.data.get(ATTR_PIN_CODE),
            "verify_mode": call.data.get(ATTR_VERIFY_MODE),
            "groups": call.data.get(ATTR_GROUPS, []),
            "start_date": call.data.get(ATTR_START_DATE),
            "end_date": call.data.get(ATTR_END_DATE),
            "status": "active",
        }
        
        # Save to storage
        await store.add_user(user_data)
        
        # Sync to all panels
        for coordinator in hass.data[DOMAIN].values():
            if hasattr(coordinator, "sync_user"):
                await coordinator.sync_user(user_data)
        
        _LOGGER.info("User added successfully")

    async def handle_update_user(call: ServiceCall) -> None:
        """Handle update user service call."""
        user_id = call.data.get("user_id")
        _LOGGER.info("Updating user: %s", user_id)
        
        store = hass.data[DOMAIN].get("store")
        if not store:
            _LOGGER.error("Storage not initialized")
            return
        
        # Update user record
        user_data = {k: v for k, v in call.data.items() if k != "user_id"}
        await store.update_user(user_id, user_data)
        
        # Sync to all panels
        for coordinator in hass.data[DOMAIN].values():
            if hasattr(coordinator, "sync_user"):
                await coordinator.sync_user(user_data)
        
        _LOGGER.info("User updated successfully")

    async def handle_delete_user(call: ServiceCall) -> None:
        """Handle delete user service call."""
        user_id = call.data.get("user_id")
        _LOGGER.info("Deleting user: %s", user_id)
        
        store = hass.data[DOMAIN].get("store")
        if not store:
            _LOGGER.error("Storage not initialized")
            return
        
        # Delete from storage
        await store.delete_user(user_id)
        
        # Remove from all panels
        for coordinator in hass.data[DOMAIN].values():
            if hasattr(coordinator, "delete_user"):
                await coordinator.delete_user(user_id)
        
        _LOGGER.info("User deleted successfully")

    async def handle_lock_all_doors(call: ServiceCall) -> None:
        """Handle lock all doors service call."""
        except_doors = call.data.get("except_doors", [])
        _LOGGER.info("Locking all doors except: %s", except_doors)
        
        for entry_id, coordinator in hass.data[DOMAIN].items():
            if not hasattr(coordinator, "lock_door"):
                continue
            
            for door_num in range(1, coordinator.door_count + 1):
                if door_num not in except_doors:
                    await coordinator.lock_door(door_num)
        
        _LOGGER.info("All doors locked")

    async def handle_unlock_all_doors(call: ServiceCall) -> None:
        """Handle unlock all doors service call."""
        only_doors = call.data.get("only_doors", [])
        duration = call.data.get("duration", 5)
        
        _LOGGER.info("Unlocking doors: %s", only_doors if only_doors else "all")
        
        for entry_id, coordinator in hass.data[DOMAIN].items():
            if not hasattr(coordinator, "unlock_door"):
                continue
            
            for door_num in range(1, coordinator.door_count + 1):
                if not only_doors or door_num in only_doors:
                    await coordinator.unlock_door(door_num, duration)
        
        _LOGGER.info("Doors unlocked")

    # Register services
    hass.services.async_register(
        DOMAIN,
        SERVICE_ADD_USER,
        handle_add_user,
        schema=SERVICE_ADD_USER_SCHEMA,
    )
    
    hass.services.async_register(
        DOMAIN,
        SERVICE_UPDATE_USER,
        handle_update_user,
        schema=SERVICE_UPDATE_USER_SCHEMA,
    )
    
    hass.services.async_register(
        DOMAIN,
        SERVICE_DELETE_USER,
        handle_delete_user,
        schema=SERVICE_DELETE_USER_SCHEMA,
    )
    
    hass.services.async_register(
        DOMAIN,
        SERVICE_LOCK_ALL_DOORS,
        handle_lock_all_doors,
        schema=SERVICE_LOCK_ALL_SCHEMA,
    )
    
    hass.services.async_register(
        DOMAIN,
        SERVICE_UNLOCK_ALL_DOORS,
        handle_unlock_all_doors,
        schema=SERVICE_UNLOCK_ALL_SCHEMA,
    )
    
    _LOGGER.info("ZKAccess services registered")
