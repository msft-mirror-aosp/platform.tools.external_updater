#
# Copyright (C) 2018 The Android Open Source Project
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import enum
import sys

USE_COLOR = sys.stdout.isatty()


@enum.unique
class Color(enum.Enum):
    """Colors for output to console."""
    FRESH = '\x1b[32m'
    STALE = '\x1b[31;1m'
    ERROR = '\x1b[31m'


END_COLOR = '\033[0m'


def color_string(string: str, color: Color) -> str:
    """Changes the color of a string when print to terminal."""
    if not USE_COLOR:
        return string
    return color.value + string + END_COLOR
