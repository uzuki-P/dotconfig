# T3 Code themes

Use these values when the user asks for a T3 Code theme. The built-in palette IDs and the T3 Chat values are copied from `packages/shared/src/themePalettes.ts` in the T3 Code source.

## Six built-in themes

The default is `t3-chat` / **T3 Chat**, the pink palette below. These are the six themes shown in T3 Code's Themes UI:

- `t3-code` / T3 Code
- `t3-chat` / T3 Chat (default)
- `grove` / Grove
- `ocean` / Ocean
- `ember` / Ember
- `iris` / Iris

`t3-code` is the mobile app's hand-tuned default palette, while the other five are the shared built-in theme definitions. For web scaffolds, T3 Chat is the default reference palette.

## Optional shadcn controls

These controls are separate from the six T3 Code palettes:

- `theme` selects the accent color family.
- `style` selects component geometry and spacing: `nova`, `vega`, `maia`, `lyra`, `mira`, `luma`, `sera`, or `rhea`.
- `baseColor` selects the neutral foundation: `neutral`, `stone`, `zinc`, `gray`, `mauve`, `olive`, `mist`, or `taupe`.

## Switch T3 themes later

For `t3-code`, `grove`, `ocean`, `ember`, or `iris`, use the corresponding T3 palette from the T3 Code source and replace the light/dark semantic token values in the theme override. Keep the shadcn component classes semantic.

For a generic shadcn accent theme, create or choose a shadcn preset code with the same Base UI, style, fonts, and Phosphor icon settings, then apply only its theme:

```bash
bun x --bun shadcn@latest apply --preset <PRESET_CODE> --only theme
```

Review the CSS diff afterward. Keep the T3-specific surface hierarchy and custom roles (`surface-raised`, `message-surface`, and `sidebar`) unless the user explicitly asks to replace the T3 Chat visual language. Use semantic classes such as `bg-background`, `bg-card`, `bg-primary`, and `bg-accent` so the switch does not require component rewrites.

The standard shadcn mapping is:

| T3 role | shadcn variable |
| --- | --- |
| `canvas` | `--background` |
| `text` | `--foreground` |
| `surface` | `--card` |
| `surfaceOverlay` | `--popover` |
| `messageAction` | `--primary` |
| `accentSurface` | `--accent` |
| `secondary` | `--secondary` |
| `muted` | `--muted` |
| `border` | `--border` |
| `input` | `--input` |
| `focus` | `--ring` |
| `error` | `--destructive` |
| `errorForeground` | `--destructive-foreground` |

## Theme color catalog

Each block below contains the semantic color values needed to reproduce that T3 Code palette in a shadcn app. The T3 Code stock palette uses hex values; the shared themes use canonical OKLCH values from the source.

| Theme | Light canvas | Light surface | Light action | Dark canvas | Dark surface | Dark action |
| --- | --- | --- | --- | --- | --- | --- |
| `t3-code` / T3 Code | `#fcfcfc` | `#ffffff` | `#1b4ed8` | `#0a0a0a` | `#111111` | `#346bf1` |
| `t3-chat` / T3 Chat | `oklch(0.982446 0.010114 325.653)` | `oklch(0.971835 0.012884 321.894)` | `oklch(0.591646 0.217985 0.584)` | `oklch(0.22813 0.020366 307.469)` | `oklch(0.267101 0.02016 311.799)` | `oklch(0.460685 0.185347 4.099)` |
| `grove` / Grove | `oklch(0.972369 0.005497 157.15)` | `oklch(0.972369 0.005497 157.15)` | `oklch(0.535028 0.106403 77.549)` | `oklch(0.260865 0.02152 162.75)` | `oklch(0.260865 0.02152 162.75)` | `oklch(0.791603 0.129713 83.299)` |
| `ocean` / Ocean | `oklch(0.974199 0.002856 241.597)` | `oklch(0.974199 0.002856 241.597)` | `oklch(0.493961 0.08175 201.584)` | `oklch(0.242641 0.024125 250.573)` | `oklch(0.242641 0.024125 250.573)` | `oklch(0.793363 0.105022 199.893)` |
| `ember` / Ember | `oklch(0.976527 0.002685 60.725)` | `oklch(0.976527 0.002685 60.725)` | `oklch(0.516323 0.161628 24.82)` | `oklch(0.245899 0.019144 42.044)` | `oklch(0.245899 0.019144 42.044)` | `oklch(0.747955 0.135578 29.432)` |
| `iris` / Iris | `oklch(0.976531 0.003855 303.226)` | `oklch(0.976531 0.003855 303.226)` | `oklch(0.516084 0.185229 340.776)` | `oklch(0.225975 0.031062 293.741)` | `oklch(0.225975 0.031062 293.741)` | `oklch(0.789904 0.130063 337.621)` |

Use the complete blocks when applying a theme. `--background`, `--card`, and `--sidebar` control the surface hierarchy; `--primary` maps to the message action color; `--accent` maps to the softer accent surface.

### `t3-code` / T3 Code

```css
:root {
  --background: #fcfcfc;
  --foreground: #27272a;
  --card: #ffffff;
  --card-foreground: #27272a;
  --popover: #ffffff;
  --popover-foreground: #27272a;
  --primary: #1b4ed8;
  --primary-foreground: #ffffff;
  --secondary: #fafafa;
  --secondary-foreground: #27272a;
  --muted: #fafafa;
  --muted-foreground: #71717b;
  --accent: #f4f4f5;
  --accent-foreground: #18181b;
  --border: #e4e4e7;
  --input: #d4d4d8;
  --ring: #1b4ed8;
  --destructive: #fb2c36;
  --destructive-foreground: #c10007;
  --surface-raised: #fcfcfc;
  --message-surface: #f4f4f5;
  --message-foreground: #27272a;
  --message-action-hover: #3160db;
  --sidebar: #fafafa;
  --sidebar-foreground: #27272a;
  --sidebar-muted-foreground: #71717b;
  --sidebar-control-surface: #f4f4f5;
  --sidebar-row-hover: #fcfcfc;
  --sidebar-row-active: #ffffff;
  --sidebar-row-selected: #ffffff;
  --sidebar-border: #e4e4e7;
}

.dark {
  --background: #0a0a0a;
  --foreground: #f5f5f5;
  --card: #111111;
  --card-foreground: #f5f5f5;
  --popover: #191919;
  --popover-foreground: #f5f5f5;
  --primary: #346bf1;
  --primary-foreground: #ffffff;
  --secondary: #141414;
  --secondary-foreground: #f5f5f5;
  --muted: #141414;
  --muted-foreground: #818181;
  --accent: #141414;
  --accent-foreground: #f5f5f5;
  --border: #191919;
  --input: #1e1e1e;
  --ring: #346bf1;
  --destructive: #fb414a;
  --destructive-foreground: #ff6467;
  --surface-raised: #141414;
  --message-surface: #141414;
  --message-foreground: #f5f5f5;
  --message-action-hover: #3061d9;
  --sidebar: #000000;
  --sidebar-foreground: #f1f3f7;
  --sidebar-muted-foreground: #a3a3a3;
  --sidebar-control-surface: #0a0a0a;
  --sidebar-row-hover: #131313;
  --sidebar-row-active: #1a1b1b;
  --sidebar-row-selected: #111111;
  --sidebar-border: #141414;
}
```

### `t3-chat` / T3 Chat

```css
:root {
  --background: oklch(0.982446 0.010114 325.653);
  --foreground: oklch(0.325698 0.116116 325.037);
  --card: oklch(0.971835 0.012884 321.894);
  --card-foreground: oklch(0.325698 0.116116 325.037);
  --popover: oklch(1 0 0);
  --popover-foreground: oklch(0.325698 0.116116 325.037);
  --primary: oklch(0.591646 0.217985 0.584);
  --primary-foreground: oklch(1 0 0);
  --secondary: oklch(0.869588 0.06751 334.899);
  --secondary-foreground: oklch(0.444777 0.134061 324.799);
  --muted: oklch(0.802407 0.090963 345.892);
  --muted-foreground: oklch(0.428932 0.163929 354.332);
  --accent: oklch(0.939552 0.024286 321.664);
  --accent-foreground: oklch(0.396296 0.025134 285.196);
  --border: oklch(0.923531 0.021247 328.096);
  --input: oklch(0.851713 0.055822 336.6);
  --ring: oklch(0.591646 0.217985 0.584);
  --destructive: oklch(0.627117 0.248974 7.734);
  --destructive-foreground: oklch(0.458704 0.169677 3.815);
  --surface-raised: oklch(0.988235 0.005049 325.615);
  --message-surface: oklch(0.926746 0.037898 332.6);
  --message-foreground: oklch(0.354591 0.093575 307.568);
  --message-action-hover: oklch(0.539042 0.197866 0.305);
  --sidebar: oklch(0.928886 0.031178 322.592);
  --sidebar-foreground: oklch(0.396296 0.025134 285.196);
  --sidebar-muted-foreground: oklch(0.494754 0.190937 354.544);
  --sidebar-control-surface: oklch(0.978851 0.001321 106.424);
  --sidebar-row-hover: oklch(0.978851 0.001321 106.424);
  --sidebar-row-active: oklch(0.978851 0.001321 106.424);
  --sidebar-row-selected: oklch(0.978851 0.001321 106.424);
  --sidebar-border: oklch(0.938313 0.002552 48.717);
}

.dark {
  --background: oklch(0.22813 0.020366 307.469);
  --foreground: oklch(0.980735 0.004092 301.426);
  --card: oklch(0.267101 0.02016 311.799);
  --card-foreground: oklch(0.980735 0.004092 301.426);
  --popover: oklch(0.154761 0.01316 338.901);
  --popover-foreground: oklch(0.980735 0.004092 301.426);
  --primary: oklch(0.460685 0.185347 4.099);
  --primary-foreground: oklch(0.901233 0.057189 343.694);
  --secondary: oklch(0.313674 0.030572 310.061);
  --secondary-foreground: oklch(0.848252 0.038248 307.961);
  --muted: oklch(0.360924 0.021469 316.83);
  --muted-foreground: oklch(0.880303 0.03077 342.696);
  --accent: oklch(0.364912 0.050794 308.491);
  --accent-foreground: oklch(0.964695 0.009139 341.803);
  --border: oklch(0.266943 0.015262 302.425);
  --input: oklch(0.266817 0.02897 344.461);
  --ring: oklch(0.591646 0.217985 0.584);
  --destructive: oklch(0.458704 0.169677 3.815);
  --destructive-foreground: oklch(0.901233 0.057189 343.694);
  --surface-raised: oklch(0.279864 0.021572 309.532);
  --message-surface: oklch(0.273791 0.025541 309.079);
  --message-foreground: oklch(0.949872 0.021269 306.838);
  --message-action-hover: oklch(0.458754 0.184639 3.857);
  --sidebar: oklch(0.185778 0.019368 322.159);
  --sidebar-foreground: oklch(0.967434 0.001326 286.375);
  --sidebar-muted-foreground: oklch(0.880303 0.03077 342.696);
  --sidebar-control-surface: oklch(0.23366 0.026081 338.196);
  --sidebar-row-hover: oklch(0.23366 0.026081 338.196);
  --sidebar-row-active: oklch(0.23366 0.026081 338.196);
  --sidebar-row-selected: oklch(0.23366 0.026081 338.196);
  --sidebar-border: oklch(0.269132 0.030766 351.067);
}
```

### `grove` / Grove

```css
:root {
  --background: oklch(0.972369 0.005497 157.15);
  --foreground: oklch(0.222003 0.03479 328.979);
  --card: oklch(0.972369 0.005497 157.15);
  --card-foreground: oklch(0.222003 0.03479 328.979);
  --popover: oklch(0.932695 0.003778 160.944);
  --popover-foreground: oklch(0.222003 0.03479 328.979);
  --primary: oklch(0.535028 0.106403 77.549);
  --primary-foreground: oklch(0.990339 0.008411 325.64);
  --secondary: oklch(0.936464 0.014601 163.554);
  --secondary-foreground: oklch(0.222003 0.03479 328.979);
  --muted: oklch(0.945455 0.012308 162.879);
  --muted-foreground: oklch(0.527266 0.012309 320.683);
  --accent: oklch(0.909438 0.021521 164.612);
  --accent-foreground: oklch(0.222003 0.03479 328.979);
  --border: oklch(0.864831 0.01312 167.255);
  --input: oklch(0.829746 0.016084 168.234);
  --ring: oklch(0.523295 0.112292 158.089);
  --destructive: oklch(0.637823 0.237287 25.436);
  --destructive-foreground: oklch(0.509494 0.208583 28.513);
  --surface-raised: oklch(0.949276 0.004496 159.002);
  --message-surface: oklch(0.891377 0.026164 164.929);
  --message-foreground: oklch(0.222003 0.03479 328.979);
  --message-action-hover: oklch(0.488753 0.096536 77.829);
  --sidebar: oklch(0.936464 0.014601 163.554);
  --sidebar-foreground: oklch(0.222003 0.03479 328.979);
  --sidebar-muted-foreground: oklch(0.515606 0.011938 318.897);
  --sidebar-control-surface: oklch(0.88585 0.011734 166.331);
  --sidebar-row-hover: oklch(0.886676 0.027374 164.983);
  --sidebar-row-active: oklch(0.85335 0.03597 165.158);
  --sidebar-row-selected: oklch(0.836654 0.040284 165.149);
  --sidebar-border: oklch(0.860274 0.010287 168.339);
}

.dark {
  --background: oklch(0.260865 0.02152 162.75);
  --foreground: oklch(0.990339 0.008411 325.64);
  --card: oklch(0.260865 0.02152 162.75);
  --card-foreground: oklch(0.990339 0.008411 325.64);
  --popover: oklch(0.411828 0.014378 166.627);
  --popover-foreground: oklch(0.990339 0.008411 325.64);
  --primary: oklch(0.791603 0.129713 83.299);
  --primary-foreground: oklch(0.222003 0.03479 328.979);
  --secondary: oklch(0.380487 0.048313 159.608);
  --secondary-foreground: oklch(0.990339 0.008411 325.64);
  --muted: oklch(0.339728 0.039456 160.274);
  --muted-foreground: oklch(0.715427 0.010896 171.428);
  --accent: oklch(0.437021 0.060312 158.962);
  --accent-foreground: oklch(0.990339 0.008411 325.64);
  --border: oklch(0.457475 0.044046 160.971);
  --input: oklch(0.519849 0.049896 160.863);
  --ring: oklch(0.796228 0.133058 157.319);
  --destructive: oklch(0.655108 0.221148 23.473);
  --destructive-foreground: oklch(0.704237 0.187511 22.228);
  --surface-raised: oklch(0.363192 0.016572 165.32);
  --message-surface: oklch(0.470111 0.067221 158.676);
  --message-foreground: oklch(0.990339 0.008411 325.64);
  --message-action-hover: oklch(0.815227 0.117902 84.21);
  --sidebar: oklch(0.309925 0.032827 160.944);
  --sidebar-foreground: oklch(0.990339 0.008411 325.64);
  --sidebar-muted-foreground: oklch(0.711387 0.007643 175.89);
  --sidebar-control-surface: oklch(0.432727 0.024549 163.654);
  --sidebar-row-hover: oklch(0.374959 0.047124 159.686);
  --sidebar-row-active: oklch(0.41688 0.056069 159.165);
  --sidebar-row-selected: oklch(0.437466 0.060406 158.958);
  --sidebar-border: oklch(0.569253 0.015933 167.062);
}
```

### `ocean` / Ocean

```css
:root {
  --background: oklch(0.974199 0.002856 241.597);
  --foreground: oklch(0.222003 0.03479 328.979);
  --card: oklch(0.974199 0.002856 241.597);
  --card-foreground: oklch(0.222003 0.03479 328.979);
  --popover: oklch(0.934442 0.003181 269.1);
  --popover-foreground: oklch(0.222003 0.03479 328.979);
  --primary: oklch(0.493961 0.08175 201.584);
  --primary-foreground: oklch(0.990339 0.008411 325.64);
  --secondary: oklch(0.939254 0.01193 241.729);
  --secondary-foreground: oklch(0.222003 0.03479 328.979);
  --muted: oklch(0.948004 0.009649 241.695);
  --muted-foreground: oklch(0.528741 0.01828 313.823);
  --accent: oklch(0.91295 0.018827 241.836);
  --accent-foreground: oklch(0.222003 0.03479 328.979);
  --border: oklch(0.867646 0.013482 252.362);
  --input: oklch(0.832939 0.017389 252.598);
  --ring: oklch(0.536684 0.120219 247.01);
  --destructive: oklch(0.637823 0.237287 25.436);
  --destructive-foreground: oklch(0.509494 0.208583 28.513);
  --surface-raised: oklch(0.951058 0.002962 258.339);
  --message-surface: oklch(0.895373 0.023469 241.913);
  --message-foreground: oklch(0.222003 0.03479 328.979);
  --message-action-hover: oklch(0.45151 0.074407 201.516);
  --sidebar: oklch(0.939254 0.01193 241.729);
  --sidebar-foreground: oklch(0.222003 0.03479 328.979);
  --sidebar-muted-foreground: oklch(0.517366 0.018944 311.433);
  --sidebar-control-surface: oklch(0.888479 0.011475 251.638);
  --sidebar-row-hover: oklch(0.890798 0.024681 241.933);
  --sidebar-row-active: oklch(0.858363 0.033325 242.089);
  --sidebar-row-selected: oklch(0.842113 0.037689 242.174);
  --sidebar-border: oklch(0.862823 0.011384 256.926);
}

.dark {
  --background: oklch(0.242641 0.024125 250.573);
  --foreground: oklch(0.990339 0.008411 325.64);
  --card: oklch(0.242641 0.024125 250.573);
  --card-foreground: oklch(0.990339 0.008411 325.64);
  --popover: oklch(0.398517 0.018232 255.72);
  --popover-foreground: oklch(0.990339 0.008411 325.64);
  --primary: oklch(0.793363 0.105022 199.893);
  --primary-foreground: oklch(0.222003 0.03479 328.979);
  --secondary: oklch(0.358725 0.043145 244.911);
  --secondary-foreground: oklch(0.990339 0.008411 325.64);
  --muted: oklch(0.319287 0.036766 246.065);
  --muted-foreground: oklch(0.691936 0.016294 261.588);
  --accent: oklch(0.413315 0.051874 243.855);
  --accent-foreground: oklch(0.990339 0.008411 325.64);
  --border: oklch(0.438653 0.039496 245.44);
  --input: oklch(0.500905 0.043574 244.781);
  --ring: oklch(0.758933 0.105833 241.548);
  --destructive: oklch(0.655108 0.221148 23.473);
  --destructive-foreground: oklch(0.702184 0.189226 22.228);
  --surface-raised: oklch(0.348439 0.019942 253.696);
  --message-surface: oklch(0.445224 0.056936 243.413);
  --message-foreground: oklch(0.990339 0.008411 325.64);
  --message-action-hover: oklch(0.815308 0.096174 199.862);
  --sidebar: oklch(0.290387 0.032043 247.274);
  --sidebar-foreground: oklch(0.990339 0.008411 325.64);
  --sidebar-muted-foreground: oklch(0.69099 0.01395 266.424);
  --sidebar-control-surface: oklch(0.417822 0.02535 250.162);
  --sidebar-row-hover: oklch(0.353381 0.042285 245.043);
  --sidebar-row-active: oklch(0.393878 0.048778 244.179);
  --sidebar-row-selected: oklch(0.413744 0.051943 243.848);
  --sidebar-border: oklch(0.55859 0.019001 256.223);
}
```

### `ember` / Ember

```css
:root {
  --background: oklch(0.976527 0.002685 60.725);
  --foreground: oklch(0.222003 0.03479 328.979);
  --card: oklch(0.976527 0.002685 60.725);
  --card-foreground: oklch(0.222003 0.03479 328.979);
  --popover: oklch(0.936659 0.002879 29.96);
  --popover-foreground: oklch(0.222003 0.03479 328.979);
  --primary: oklch(0.516323 0.161628 24.82);
  --primary-foreground: oklch(0.990339 0.008411 325.64);
  --secondary: oklch(0.942267 0.01151 50.785);
  --secondary-foreground: oklch(0.222003 0.03479 328.979);
  --muted: oklch(0.950842 0.009273 51.528);
  --muted-foreground: oklch(0.530413 0.018453 341.181);
  --accent: oklch(0.916502 0.01832 49.597);
  --accent-foreground: oklch(0.222003 0.03479 328.979);
  --border: oklch(0.870631 0.013204 39.431);
  --input: oklch(0.836213 0.017153 38.661);
  --ring: oklch(0.552831 0.129438 44.656);
  --destructive: oklch(0.637823 0.237287 25.436);
  --destructive-foreground: oklch(0.509494 0.208583 28.513);
  --surface-raised: oklch(0.953321 0.002701 42.266);
  --message-surface: oklch(0.899296 0.022939 49.163);
  --message-foreground: oklch(0.222003 0.03479 328.979);
  --message-action-hover: oklch(0.471223 0.145843 24.688);
  --sidebar: oklch(0.942267 0.01151 50.785);
  --sidebar-foreground: oklch(0.222003 0.03479 328.979);
  --sidebar-muted-foreground: oklch(0.519146 0.019214 343.427);
  --sidebar-control-surface: oklch(0.891332 0.011179 40.596);
  --sidebar-row-hover: oklch(0.894819 0.024151 49.073);
  --sidebar-row-active: oklch(0.863104 0.032855 48.586);
  --sidebar-row-selected: oklch(0.84723 0.037292 48.403);
  --sidebar-border: oklch(0.865593 0.011154 35.246);
}

.dark {
  --background: oklch(0.245899 0.019144 42.044);
  --foreground: oklch(0.990339 0.008411 325.64);
  --card: oklch(0.245899 0.019144 42.044);
  --card-foreground: oklch(0.990339 0.008411 325.64);
  --popover: oklch(0.401111 0.014308 34.896);
  --popover-foreground: oklch(0.990339 0.008411 325.64);
  --primary: oklch(0.747955 0.135578 29.432);
  --primary-foreground: oklch(0.222003 0.03479 328.979);
  --secondary: oklch(0.361499 0.044052 49.515);
  --secondary-foreground: oklch(0.990339 0.008411 325.64);
  --muted: oklch(0.322144 0.03574 48.309);
  --muted-foreground: oklch(0.692479 0.015227 30.963);
  --accent: oklch(0.416048 0.055354 50.484);
  --accent-foreground: oklch(0.990339 0.008411 325.64);
  --border: oklch(0.44099 0.040202 48.807);
  --input: oklch(0.503003 0.045721 49.44);
  --ring: oklch(0.762174 0.124117 52.082);
  --destructive: oklch(0.655108 0.221148 23.473);
  --destructive-foreground: oklch(0.702184 0.189226 22.228);
  --surface-raised: oklch(0.351262 0.01565 37.592);
  --message-surface: oklch(0.447961 0.061874 50.849);
  --message-foreground: oklch(0.990339 0.008411 325.64);
  --message-action-hover: oklch(0.775116 0.117953 29.014);
  --sidebar: oklch(0.293349 0.029554 46.882);
  --sidebar-foreground: oklch(0.990339 0.008411 325.64);
  --sidebar-muted-foreground: oklch(0.691874 0.012538 24.638);
  --sidebar-control-surface: oklch(0.420227 0.022893 43.226);
  --sidebar-row-hover: oklch(0.356163 0.042933 49.385);
  --sidebar-row-active: oklch(0.396617 0.051353 50.201);
  --sidebar-row-selected: oklch(0.416477 0.055442 50.489);
  --sidebar-border: oklch(0.560372 0.016998 36.179);
}
```

### `iris` / Iris

```css
:root {
  --background: oklch(0.976531 0.003855 303.226);
  --foreground: oklch(0.222003 0.03479 328.979);
  --card: oklch(0.976531 0.003855 303.226);
  --card-foreground: oklch(0.222003 0.03479 328.979);
  --popover: oklch(0.936665 0.005041 310.132);
  --popover-foreground: oklch(0.222003 0.03479 328.979);
  --primary: oklch(0.516084 0.185229 340.776);
  --primary-foreground: oklch(0.990339 0.008411 325.64);
  --secondary: oklch(0.941387 0.014687 300.474);
  --secondary-foreground: oklch(0.222003 0.03479 328.979);
  --muted: oklch(0.950194 0.011956 300.733);
  --muted-foreground: oklch(0.529955 0.022319 321.556);
  --accent: oklch(0.914882 0.022965 299.986);
  --accent-foreground: oklch(0.222003 0.03479 328.979);
  --border: oklch(0.869608 0.018226 303.859);
  --input: oklch(0.834773 0.023405 303.676);
  --ring: oklch(0.525348 0.15373 294.176);
  --destructive: oklch(0.637823 0.237287 25.436);
  --destructive-foreground: oklch(0.509494 0.208583 28.513);
  --surface-raised: oklch(0.953326 0.004536 307.676);
  --message-surface: oklch(0.897143 0.028558 299.758);
  --message-foreground: oklch(0.222003 0.03479 328.979);
  --message-action-hover: oklch(0.471003 0.16748 340.687);
  --sidebar: oklch(0.941387 0.014687 300.474);
  --sidebar-foreground: oklch(0.222003 0.03479 328.979);
  --sidebar-muted-foreground: oklch(0.518417 0.023683 320.681);
  --sidebar-control-surface: oklch(0.890512 0.0155 303.803);
  --sidebar-row-hover: oklch(0.892522 0.030022 299.704);
  --sidebar-row-active: oklch(0.85971 0.040501 299.36);
  --sidebar-row-selected: oklch(0.843236 0.045818 299.198);
  --sidebar-border: oklch(0.864805 0.015938 305.371);
}

.dark {
  --background: oklch(0.225975 0.031062 293.741);
  --foreground: oklch(0.990339 0.008411 325.64);
  --card: oklch(0.225975 0.031062 293.741);
  --card-foreground: oklch(0.990339 0.008411 325.64);
  --popover: oklch(0.386739 0.024023 297.509);
  --popover-foreground: oklch(0.990339 0.008411 325.64);
  --primary: oklch(0.789904 0.130063 337.621);
  --primary-foreground: oklch(0.222003 0.03479 328.979);
  --secondary: oklch(0.325405 0.063614 294.23);
  --secondary-foreground: oklch(0.990339 0.008411 325.64);
  --muted: oklch(0.291515 0.05276 294.209);
  --muted-foreground: oklch(0.663321 0.025932 301.862);
  --accent: oklch(0.372436 0.07841 294.204);
  --accent-foreground: oklch(0.990339 0.008411 325.64);
  --border: oklch(0.40874 0.058536 295.893);
  --input: oklch(0.46756 0.065775 296.265);
  --ring: oklch(0.671712 0.169136 293.929);
  --destructive: oklch(0.655108 0.221148 23.473);
  --destructive-foreground: oklch(0.702184 0.189226 22.228);
  --surface-raised: oklch(0.335291 0.026008 296.394);
  --message-surface: oklch(0.399975 0.086965 294.177);
  --message-foreground: oklch(0.990339 0.008411 325.64);
  --message-action-hover: oklch(0.813537 0.114101 337.23);
  --sidebar: oklch(0.266743 0.044689 294.138);
  --sidebar-foreground: oklch(0.990339 0.008411 325.64);
  --sidebar-muted-foreground: oklch(0.668773 0.021522 302.949);
  --sidebar-control-surface: oklch(0.399977 0.035678 297.031);
  --sidebar-row-hover: oklch(0.320808 0.062152 294.23);
  --sidebar-row-active: oklch(0.355677 0.073167 294.217);
  --sidebar-row-selected: oklch(0.372806 0.078525 294.203);
  --sidebar-border: oklch(0.545895 0.027522 299.871);
}
```

Load the selected override after the generated shadcn stylesheet. Keep component classes semantic, for example `bg-background`, `bg-card`, `bg-primary`, `bg-accent`, and `text-muted-foreground`. Do not hardcode one palette inside individual components.
