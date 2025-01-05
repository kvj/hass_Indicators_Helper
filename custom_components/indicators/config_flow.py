from collections.abc import Mapping
from typing import Any, cast

from homeassistant import config_entries
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.selector import selector
from homeassistant.util.yaml.loader import parse_yaml

from homeassistant.const import (
    CONF_NAME,
)

from homeassistant.helpers.schema_config_entry_flow import (
    SchemaConfigFlowHandler,
    SchemaFlowFormStep,
    SchemaFlowError,
)

from .constants import *

import voluptuous as vol
import logging

_LOGGER = logging.getLogger(__name__)

DEF_TEMPLATE = """
rows:
  - cols:
      - entity_id: sensor.sun_solar_rising
""".strip()

OPTIONS_SCHEMA = vol.Schema({
    vol.Required(CONF_ROWS, description={"suggested_value": 5}): selector({"number": {"min": 1, "max": 99}}),
    vol.Required(CONF_COLS, description={"suggested_value": 5}): selector({"number": {"min": 1, "max": 99}}),
    vol.Required(CONF_SIZE, description={"suggested_value": 50}): selector({"number": {"min": 5, "max": 200, "unit_of_measurement": "px"}}),
    vol.Required(CONF_GAP, description={"suggested_value": 5}): selector({"number": {"min": 0, "max": 100, "unit_of_measurement": "px"}}),
    vol.Required(CONF_PADDING, description={"suggested_value": 5}): selector({"number": {"min": 0, "max": 100, "unit_of_measurement": "px"}}),
    vol.Required(CONF_SHAPE, description={"suggested_value": CONF_SHAPE_SQ}): selector({"select": {
        "options": [
            {"label": "Square", "value": CONF_SHAPE_SQ}, 
            {"label": "Rounded Square", "value": CONF_SHAPE_RS}, 
            {"label": "Circle", "value": CONF_SHAPE_CL},
        ],
        "translation_key": "shape",
    }}),
    vol.Required(CONF_BG_COLOR, description={"suggested_value": [0x42, 0x42, 0x42]}): selector({"color_rgb": {}}),
    vol.Required(CONF_BG_TRANSP, description={"suggested_value": True}): selector({"boolean": {}}),
    vol.Required(CONF_OFF_COLOR, description={"suggested_value": [0x21, 0x21, 0x21]}): selector({"color_rgb": {}}),
    vol.Required(CONF_OFF_TRANSP, description={"suggested_value": False}): selector({"boolean": {}}),
    vol.Required(CONF_ON_COLOR, description={"suggested_value": [0xFF, 0xEB, 0x3B]}): selector({"color_rgb": {}}),
    vol.Required(CONF_TEMPLATE, description={"suggested_value": DEF_TEMPLATE}): selector({"template": {}}),
})

CONFIG_SCHEMA = vol.Schema({
    vol.Required(CONF_NAME): selector({"text": {}}),
}).extend(OPTIONS_SCHEMA.schema)

async def _validate_options(step, user_input):
    _LOGGER.debug(f"_validate_options: {user_input}, {step}, {step.options}")
    try:
        yaml_obj = parse_yaml(user_input[CONF_TEMPLATE])
        user_input[CONF_TEMPLATE_YAML] = yaml_obj
    except:
        _LOGGER.exception(f"_validate_options: Invalid yaml")
        raise SchemaFlowError("invalid_yaml")
    return user_input

CONFIG_FLOW = {
    "user": SchemaFlowFormStep(CONFIG_SCHEMA, _validate_options),
}

OPTIONS_FLOW = {
    "init": SchemaFlowFormStep(OPTIONS_SCHEMA, _validate_options),
}

class ConfigFlowHandler(SchemaConfigFlowHandler, domain=DOMAIN):

    config_flow = CONFIG_FLOW
    options_flow = OPTIONS_FLOW

    def async_config_entry_title(self, options: Mapping[str, Any]) -> str:
        return cast(str, options[CONF_NAME])
