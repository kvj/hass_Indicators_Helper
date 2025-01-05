from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
)
from homeassistant.helpers import (
    entity_registry,
    device_registry,
    event,
    template,
)
from homeassistant.exceptions import HomeAssistantError

from homeassistant.const import (
    CONF_NAME,
)


from .constants import *

import logging
from datetime import datetime

_LOGGER = logging.getLogger(__name__)

class Coordinator(DataUpdateCoordinator):

    def __init__(self, hass, entry):
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_method=self._async_update,
        )
        self._entry = entry
        self._entry_id = entry.entry_id
        self._on_entity_state_handler = None

    def _disable_listener(self, listener):
        if listener:
            listener()
        return None

    async def _async_update(self):
        return {}
    
    def _find_entity_ids(self, config):
        ids = set()
        for r in config.get("rows", []):
            for c in r.get("cols", []):
                if "entity_id" in c:
                    ids.add(c["entity_id"])
                if "entity_ids" in c:
                    ids.update(c.get("entity_ids", []))
        _LOGGER.debug(f"_find_entity_ids: {ids}, {config}")
        return list(ids)

    async def _async_on_state_change(self, entity_id: str, from_state, to_state):
        _LOGGER.debug(f"_async_on_state_change: {entity_id}")
        self._trigger_image_update()

    def _trigger_image_update(self):
        self.async_set_updated_data({
            **self.data,
            "last_update": datetime.now(),
        })

    async def async_load(self):
        self._config = self._entry.as_dict()["options"]
        _LOGGER.debug(f"async_load: {self._config}")
        self._on_entity_state_handler = event.async_track_state_change(
            self.hass,
            self._find_entity_ids(self._config[CONF_TEMPLATE_YAML]),
            action=self._async_on_state_change
        )
        self._trigger_image_update()

    async def _async_build_value(self, item):
        if not item or item is False or item == "" or item == 0:
            return None
        state = None
        if "entity_id" in item:
            state = self.hass.states.get(item["entity_id"])
        value = state.state if state else "off"
        if "value_template"in item:
            tmpl = template.Template(item["value_template"], self.hass)
            value = template.render_complex(tmpl, {"state": state})
        is_on = value == "on" or value is True
        if not is_on:
            return None
        color = item.get("color", tuple(self._config[CONF_ON_COLOR]))
        if "color_template" in item:
            tmpl = template.Template(item["color_template"], self.hass)
            color = template.render_complex(tmpl, {"state": state})
        if not color:
            return None
        return color

    async def async_build(self):
        result = [[None for _ in range(int(self._config[CONF_COLS]))] for _ in range(int(self._config[CONF_ROWS]))]
        rows = self._config[CONF_TEMPLATE_YAML].get("rows", [])
        for j in range(len(rows)):
            cols = rows[j].get("cols", [])
            for i in range(len(cols)):
                result[j][i] = await self._async_build_value(cols[i])
        return result

    async def async_unload(self):
        _LOGGER.debug(f"async_unload:")
        self._on_entity_state_handler = self._disable_listener(self._on_entity_state_handler)

    @property
    def entity_name(self):
        return self._config[CONF_NAME]
