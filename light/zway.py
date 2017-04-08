"""
Z-Way Light Component for Home Assistant
https://github.com/jschlyter/hass-zway

Copyright (c) 2017 Jakob Schlyter. All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions
are met:
1. Redistributions of source code must retain the above copyright
   notice, this list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright
   notice, this list of conditions and the following disclaimer in the
   documentation and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR
IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY
DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE
GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN
IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

import logging

import voluptuous as vol

# Import the device class from the component that you want to support
import homeassistant.util.color as color_util
from homeassistant.components.light import (
    ATTR_BRIGHTNESS, ATTR_RGB_COLOR,
    SUPPORT_BRIGHTNESS, SUPPORT_RGB_COLOR,
    Light, PLATFORM_SCHEMA)
from homeassistant.const import CONF_URL, CONF_USERNAME, CONF_PASSWORD, CONF_INCLUDE
import homeassistant.helpers.config_validation as cv

# Home Assistant depends on 3rd party packages for API specific code.
REQUIREMENTS = ['zway==0.1']

_LOGGER = logging.getLogger(__name__)

# Validation of the user's configuration
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_URL): cv.string,
    vol.Optional(CONF_USERNAME, default='admin'): cv.string,
    vol.Optional(CONF_PASSWORD): cv.string,
    vol.Optional(CONF_INCLUDE): cv.string
})

SUPPORT_ZWAY = {
    'switchBinary': 0,
    'switchMultilevel': SUPPORT_BRIGHTNESS,
    'switchRGBW': SUPPORT_RGB_COLOR
}


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup Z-Way Light platform."""
    from zway.controller import Controller
    import zway.devices

    zwc = Controller(baseurl=config.get(CONF_URL),
                     username=config.get(CONF_USERNAME),
                     password=config.get(CONF_PASSWORD))

    include = config.get(CONF_INCLUDE)
    devices = []
    for dev in zwc.devices:
        if dev.is_tagged(include):
            if (isinstance(dev, zway.devices.SwitchBinary) or
                isinstance(dev, zway.devices.SwitchMultilevel) or
                isinstance(dev, zway.devices.SwitchRGBW)):
                _LOGGER.info("Including %s %s: %s", dev.devicetype, dev.id, dev.title)
                devices.append(ZWayLight(dev))
    add_devices(devices)


class ZWayLight(Light):
    """Representation of an Z-Way Light"""

    def __init__(self, device):
        self._zlight = device

    @property
    def unique_id(self):
        """Return the ID of this light."""
        return self._zlight.id.lower()

    @property
    def name(self):
        """Return the display name of this light."""
        return self._zlight.title

    @property
    def supported_features(self):
        """Flag supported features."""
        return SUPPORT_ZWAY.get(self._zlight.devicetype, 0)

    @property
    def is_on(self):
        """Return true if light is on."""
        return self._zlight.state

    @property
    def brightness(self):
        """Brightness of the light (an integer in the range 1-255)."""
        if self._zlight.devicetype == 'switchMultilevel':
            return self._zlight.level
        else:
            return None

    @property
    def rgb_color(self):
        """Return the RGB color value."""
        if self._zlight.devicetype == 'switchRGBW' and self._zlight.rgb is not None:
            return list(self._zlight.rgb)
        else:
            return None

    def turn_on(self, **kwargs):
        """Instruct the light to turn on."""
        if self._zlight.devicetype == 'switchMultilevel':
            self._zlight.level = kwargs.get(ATTR_BRIGHTNESS, 255)
        elif self._zlight.devicetype == 'switchRGBW':
            self._zlight.rgb = tuple(kwargs.get(ATTR_RGB_COLOR))
        else:
            self._zlight.state = True

    def turn_off(self, **kwargs):
        """Instruct the light to turn off."""
        self._zlight.state = False

    def update(self):
        """Fetch new state data for this light.

        This is the only method that should fetch new data for Home Assistant.
        """
        self._zlight.update()
