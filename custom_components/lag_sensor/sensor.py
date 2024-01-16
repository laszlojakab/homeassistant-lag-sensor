"""The lag sensor implementation."""
import logging
from datetime import datetime, timedelta
from functools import partial
from typing import Self

import homeassistant.util.dt as dt_util
from homeassistant.components.recorder import get_instance, history
from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_UNIT_OF_MEASUREMENT, CONF_DELAY_TIME, CONF_ENTITY_ID, CONF_NAME
from homeassistant.core import HomeAssistant, State, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import (
    EventStateChangedData,
    async_track_point_in_utc_time,
    async_track_state_change_event,
)
from homeassistant.helpers.typing import EventType

_LOGGER = logging.getLogger(__name__)


class LagSensor(SensorEntity):
    """Represents the lag sensor."""

    def __init__(self, name: str, entity_id: str, delay_time: timedelta):
        """
        Initialize a new instance of `LagSensor` class.

        Args:
            name:
                The entity name
            entity_id:
                The lagged entity id
            delay_time:
                The amount of lag
            unit_of_measurement:
                The measurement unit
        """
        self.entity_description = SensorEntityDescription(key="lag", name=name)
        self._attr_unique_id = "lag_sensor_" + entity_id + str(delay_time)
        self._attr_should_poll = False
        self._lagged_entity_id = entity_id
        self._delay_time = delay_time
        self._lagged_states: list[State] = []

    async def async_added_to_hass(self: Self) -> None:
        """Complete sensor setup after being added to hass."""

        @callback
        def lag_sensor_state_listener(
            event: EventType[EventStateChangedData],
        ) -> None:
            """Handle state changes on lagged sensor."""
            should_track_point_in_time = len(self._lagged_states) == 0

            self._lagged_states.append(event.data["new_state"])

            @callback
            def update_state(now: datetime) -> None:  # noqa: ARG001
                self._update_lagged_value()

            if should_track_point_in_time:
                async_track_point_in_utc_time(
                    self.hass, update_state, self._delay_time + self._lagged_states[0].last_updated
                )

        start = dt_util.utcnow() - self._delay_time
        lagged_history = (
            await get_instance(self.hass).async_add_executor_job(
                partial(
                    history.state_changes_during_period,
                    self.hass,
                    start,
                    entity_id=self._lagged_entity_id,
                )
            )
        )[self._lagged_entity_id]

        self._lagged_states.extend(sorted(lagged_history, key=lambda s: s.last_updated))

        if len(self._lagged_states) > 0:

            @callback
            def update_state(now: datetime) -> None:  # noqa: ARG001
                self._update_lagged_value()

            async_track_point_in_utc_time(
                self.hass, update_state, self._delay_time + self._lagged_states[0].last_updated
            )

        self.async_on_remove(
            async_track_state_change_event(
                self.hass, [self._lagged_entity_id], lag_sensor_state_listener
            )
        )

    def _update_lagged_value(self: Self) -> None:
        should_track_point_in_time = len(self._lagged_states) > 1

        new_state = self._lagged_states.pop(0)

        self._attr_native_value = new_state.state
        self._attr_native_unit_of_measurement = new_state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)
        self.schedule_update_ha_state(False)

        if should_track_point_in_time:

            @callback
            def update_state(now: datetime) -> None:  # noqa: ARG001
                self._update_lagged_value()

            async_track_point_in_utc_time(
                self.hass, update_state, self._delay_time + self._lagged_states[0].last_updated
            )


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> bool:
    """
    Setup of lag sensor for the specified config_entry.

    Args:
        hass: The Home Assistant instance.
        config_entry: The config entry which is used to create sensors.
        async_add_entities: The callback which can be used to add new entities to Home Assistant.

    Returns:
        The value indicates whether the setup succeeded.
    """
    _LOGGER.info("Setting up lag sensor: %s.", config_entry.data.get(CONF_NAME))

    async_add_entities(
        [
            LagSensor(
                config_entry.data.get(CONF_NAME),
                config_entry.data.get(CONF_ENTITY_ID),
                dt_util.parse_duration(config_entry.data.get(CONF_DELAY_TIME)),
            ),
        ]
    )

    _LOGGER.info("Setting up lag sensor completed: %s.", config_entry.data.get(CONF_NAME))
    return True
