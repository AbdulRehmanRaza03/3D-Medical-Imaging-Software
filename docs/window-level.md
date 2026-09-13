# Window / Level (CT Intensity Mapping)

CT pixel values are Hounsfield Units (HU). A raw linear display would waste most
of the intensity range on air and would clip soft tissue and bone. Window/level
remaps a sub-range of HU onto the full 8-bit display range.

## How it works

Given a window **width** `W` and window **level** `L`:

```
lower = L - W/2
upper = L + W/2

display = clip( (HU - lower) * 255 / W, 0, 255 )
```

Values below `lower` go black, above `upper` go white, and the range in between
maps linearly to grayscale.

## Presets

Common starting points (NOT universally correct for every scanner):

| Preset      | Width | Level |
| ----------- | ----- | ----- |
| Bone        | 1800  | 400   |
| Soft tissue | 400   | 40    |
| Lung        | 1500  | -600  |

These provide sensible initial visibility of the respective tissue class but
should be adjusted per study.

## Interaction

- Dedicated slider controls for width and level.
- Mouse window/level mode: horizontal drag changes width, vertical drag changes
  level (enabled via the `W` tool).
- The active window/level is applied server-side when each MPR slice is
  requested, so the intensity mapping is consistent across all views.

## Implementation

`backend/app/services/windowing_service.py` (`apply_window`) converts a
float32 HU slice to `uint8` for PNG encoding.
