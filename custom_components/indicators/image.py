from PIL import Image, ImageDraw, ImageColor
import io

from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
)

from homeassistant.components.image import ImageEntity

import logging

from .coordinator import Coordinator

from .constants import *

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, add_entities):
    coordinator = entry.runtime_data
    add_entities([_Entity(coordinator)])
    return True


class _Entity(CoordinatorEntity, ImageEntity):

    def __init__(self, coordinator: Coordinator):
        super().__init__(coordinator)
        ImageEntity.__init__(self, coordinator.hass)
        self._attr_has_entity_name = True
        self._attr_unique_id = f"indicators_{self.coordinator._entry_id}_"
        self._attr_name = self.coordinator.entity_name
        self._attr_content_type = "image/png"

    @property
    def image_last_updated(self):
        return self.coordinator.data.get("last_update")

    async def async_image(self) -> bytes | None:
        pixels = await self.coordinator.async_build()

        cols = int(self.coordinator._config[CONF_COLS])
        rows = int(self.coordinator._config[CONF_ROWS])
        padding = int(self.coordinator._config[CONF_PADDING])
        gap = int(self.coordinator._config[CONF_GAP])
        size = int(self.coordinator._config[CONF_SIZE])

        width = 2 * padding + gap * (cols - 1) + size * cols;
        height = 2 * padding + gap * (rows - 1) + size * rows;

        bg_color = tuple(self.coordinator._config[CONF_BG_COLOR] + [0x01 if self.coordinator._config[CONF_BG_TRANSP] else 0xff])
        off_color = tuple(self.coordinator._config[CONF_OFF_COLOR] + [0x01 if self.coordinator._config[CONF_OFF_TRANSP] else 0xff])

        shape = self.coordinator._config[CONF_SHAPE]

        img = Image.new("RGBA", (width, height), bg_color)
        draw = ImageDraw.Draw(img)

        for j in range(len(pixels)):
            row = pixels[j]
            y = padding + (size + gap) * j
            for i in range(len(row)):
                x = padding + (size + gap) * i

                col = off_color if row[i] is None else row[i]
                col_ = ImageColor.getrgb(col) if isinstance(col, str) else col
                # _LOGGER.debug(f"async_image: {col}, {col_}")
                if shape == CONF_SHAPE_SQ:
                    draw.rectangle([x, y, x + size, y + size], fill=tuple(col_))
                elif shape == CONF_SHAPE_RS:
                    draw.rounded_rectangle([x, y, x + size, y + size], radius=gap, fill=tuple(col_))
                elif shape == CONF_SHAPE_CL:
                    draw.circle([int(x + size / 2), int(y + size / 2)], radius=int(size / 2), fill=tuple(col_))
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="png")
        return img_bytes.getvalue()
