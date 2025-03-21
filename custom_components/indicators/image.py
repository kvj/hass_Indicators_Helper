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


class _Entity(CoordinatorEntity[Coordinator], ImageEntity):

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

    @property
    def state_attributes(self):
        super_value = super().state_attributes
        return {
            **(super_value if super_value else {}),
            "columns": int(self.coordinator._config[CONF_COLS]),
            "rows": int(self.coordinator._config[CONF_ROWS]),
            "padding": int(self.coordinator._config[CONF_PADDING]),
            "gap": int(self.coordinator._config[CONF_GAP]),
            "size": int(self.coordinator._config[CONF_SIZE]),
        }


    async def async_image(self) -> bytes | None:
        with_icons = self.coordinator._config.get(CONF_RENDER_ICONS, False)
        text_mode = self.coordinator._config.get(CONF_TEXT_MODE, False)

        cols = int(self.coordinator._config[CONF_COLS])
        rows = int(self.coordinator._config[CONF_ROWS])
        padding = int(self.coordinator._config[CONF_PADDING])
        gap = int(self.coordinator._config[CONF_GAP])
        size = int(self.coordinator._config[CONF_SIZE])
        ratio = float(self.coordinator._config.get(CONF_RATIO, 1))
        size_y = size
        size_x = int(size * ratio)

        icon_size = int(min(size_x, size_y) * 0.7)

        width = 2 * padding + gap * (cols - 1) + size_x * cols;
        height = 2 * padding + gap * (rows - 1) + size_y * rows;

        bg_color = tuple(self.coordinator._config[CONF_BG_COLOR] + [0x01 if self.coordinator._config[CONF_BG_TRANSP] else 0xff])
        off_color = tuple(self.coordinator._config[CONF_OFF_COLOR] + [0x01 if self.coordinator._config[CONF_OFF_TRANSP] else 0xff])

        shape = self.coordinator._config[CONF_SHAPE]
        if shape == CONF_SHAPE_CL and ratio != 1:
            shape = CONF_SHAPE_RS

        pixels = await self.coordinator.async_build()

        img = Image.new("RGBA", (width, height), bg_color)
        draw = ImageDraw.Draw(img)

        for j in range(len(pixels)):
            row = pixels[j]
            y = padding + (size_y + gap) * j
            for i in range(len(row)):

                _LOGGER.debug(f"async_image: {row[i]}, {i}")
                item_def, icon_def = row[i]
                x = padding + (size_x + gap) * i
                has_color = item_def != None
                col = off_color if not has_color else item_def
                if text_mode:
                    col = off_color
                col_ = ImageColor.getrgb(col) if isinstance(col, str) else col
                if shape == CONF_SHAPE_SQ:
                    draw.rectangle([x, y, x + size_x, y + size_y], fill=tuple(col_))
                elif shape == CONF_SHAPE_RS:
                    draw.rounded_rectangle([x, y, x + size_x, y + size_y], radius=gap, fill=tuple(col_))
                elif shape == CONF_SHAPE_CL:
                    draw.circle([int(x + size / 2), int(y + size / 2)], radius=int(size / 2), fill=tuple(col_))
                if with_icons and icon_def:

                    icon_, icon_size_, icon_color_ = icon_def
                    icon_size_ = icon_size_ if icon_size_ else icon_size
                    icon_color_ = icon_color_ + [0xff] if icon_color_ else (0, 0, 0, 0xff)
                    if text_mode:
                        if not has_color:
                            continue
                        icon_color_ = ImageColor.getrgb(item_def) if isinstance(item_def, str) else item_def
                    _LOGGER.debug(f"async_image: draw_icon {icon_}, {icon_size_}, {icon_color_}")
                    self.coordinator._mdi_font.draw_icon(
                        draw, icon_, icon_size_,
                        int(x + size_x / 2), int(y + size_y / 2),
                        tuple(icon_color_),
                    )
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="png")
        return img_bytes.getvalue()
