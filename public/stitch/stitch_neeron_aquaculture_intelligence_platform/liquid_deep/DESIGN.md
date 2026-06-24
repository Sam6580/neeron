---
name: Liquid Deep
colors:
  surface: '#0b1326'
  surface-dim: '#0b1326'
  surface-bright: '#31394d'
  surface-container-lowest: '#060e20'
  surface-container-low: '#131b2e'
  surface-container: '#171f33'
  surface-container-high: '#222a3d'
  surface-container-highest: '#2d3449'
  on-surface: '#dae2fd'
  on-surface-variant: '#bbc9cf'
  inverse-surface: '#dae2fd'
  inverse-on-surface: '#283044'
  outline: '#859399'
  outline-variant: '#3c494e'
  surface-tint: '#47d6ff'
  primary: '#a5e7ff'
  on-primary: '#003543'
  primary-container: '#00d2ff'
  on-primary-container: '#00566a'
  inverse-primary: '#00677f'
  secondary: '#b3c5ff'
  on-secondary: '#002a76'
  secondary-container: '#0052d3'
  on-secondary-container: '#c8d3ff'
  tertiary: '#f7d1ff'
  on-tertiary: '#520070'
  tertiary-container: '#eaaaff'
  on-tertiary-container: '#772b95'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#b6ebff'
  primary-fixed-dim: '#47d6ff'
  on-primary-fixed: '#001f28'
  on-primary-fixed-variant: '#004e60'
  secondary-fixed: '#dbe1ff'
  secondary-fixed-dim: '#b3c5ff'
  on-secondary-fixed: '#00184a'
  on-secondary-fixed-variant: '#003ea6'
  tertiary-fixed: '#f9d8ff'
  tertiary-fixed-dim: '#edb1ff'
  on-tertiary-fixed: '#320046'
  on-tertiary-fixed-variant: '#6e208c'
  background: '#0b1326'
  on-background: '#dae2fd'
  surface-variant: '#2d3449'
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  display-lg-mobile:
    fontFamily: Inter
    fontSize: 36px
    fontWeight: '700'
    lineHeight: 44px
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Inter
    fontSize: 30px
    fontWeight: '600'
    lineHeight: 38px
    letterSpacing: -0.01em
  headline-sm:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: '0'
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
    letterSpacing: '0'
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
    letterSpacing: '0'
  label-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
    letterSpacing: 0.02em
  label-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.05em
rounded:
  sm: 0.5rem
  DEFAULT: 1rem
  md: 1.5rem
  lg: 2rem
  xl: 3rem
  full: 9999px
spacing:
  unit: 8px
  container-padding-mobile: 20px
  container-padding-desktop: 40px
  gutter: 24px
  element-gap: 16px
---

## Brand & Style
The design system is centered on the concept of "Hydro-Fluidity." It evokes the calm, immersive sensation of being underwater while maintaining the precision of a high-end technical interface. The target audience values premium, atmospheric experiences that feel organic rather than mechanical.

The style is a sophisticated blend of **Glassmorphism** and **Minimalism**. It uses translucent layers to simulate light passing through water (refraction) and heavy background blurs to create a sense of depth and focus. Motion should feel viscous and easing should be soft, mimicking the natural flow of a liquid environment.

## Colors
The palette is rooted in the "Abyssal Gradient." The background uses a deep, dark navy (#0F172A) to represent the ocean floor. Primary actions utilize a bright, glowing cyan (#00D2FF) to mimic sunlight hitting the surface.

**Gradient Logic:**
- **Surface Gradients:** Use linear gradients from `secondary` to `primary` at a 135-degree angle to simulate light refraction.
- **Deep Gradients:** Use radial gradients that transition from a lighter teal center to the deep neutral background for container backgrounds.
- **Accents:** Use the purple tertiary color sparingly for high-interest notifications or rare "bioluminescent" interactions.

## Typography
This design system utilizes **Inter** exclusively to provide a clean, systematic contrast to the fluid, organic shapes of the UI. 

For high-level displays, tight letter spacing and heavy weights are used to anchor the eye amidst the soft gradients. Body text is kept at a medium weight (400) with generous line heights to ensure maximum legibility against dark, translucent backgrounds. Labels use increased letter spacing and uppercase styling to provide a technical, "instrument-panel" feel.

## Layout & Spacing
The layout follows a **Fluid Grid** model with an emphasis on "negative space as water." Elements should never feel cramped; they should feel as though they are floating within a medium.

- **Desktop:** 12-column grid, 24px gutters, max-width 1440px.
- **Tablet:** 8-column grid, 20px gutters.
- **Mobile:** 4-column grid, 16px gutters.

Use dynamic padding that increases as the screen size grows to maintain the sense of "open water." Alignment should favor the center or balanced asymmetrical compositions to reinforce the organic feel.

## Elevation & Depth
Depth is created through **Glassmorphism** rather than traditional drop shadows.

- **Base Layer:** Solid Abyssal Neutral.
- **Floating Containers:** 10% opacity white fill with a 20px - 40px Backdrop Blur.
- **Borders:** "Inner Glow" borders—1px solid strokes with 20% opacity white on the top/left and 10% opacity primary color on the bottom/right to simulate light catching the edge of a droplet.
- **Shadows:** Use "Ambient Deep" shadows—very large blur radii (60px+), low opacity (15%), and tinted with the secondary blue color to create a soft glow rather than a dark void.

## Shapes
Shapes in this design system are "Hyper-Organic." Every element must feel like a smoothed river stone or a suspended water droplet. 

Avoid sharp corners entirely. The `rounded-xl` and `rounded-pill` settings are the defaults for buttons, input fields, and tags. Large containers should use a minimum of 24px corner radius to ensure they feel soft and approachable within the deep, dark environment.

## Components
- **Buttons:** Use full pill-shapes. The primary button is a gradient from `secondary` to `primary` with a subtle white inner-top-border. On hover, the gradient should "expand," increasing the luminosity of the primary color.
- **Input Fields:** Semi-transparent "glass" backgrounds with a 1px border that brightens when focused. The cursor should be the primary cyan color.
- **Cards:** Utilize heavy background blur (Glassmorphism). Content should be grouped with generous internal padding (min 24px).
- **Chips/Badges:** Small, fully rounded pods with a subtle glow effect (`box-shadow: 0 0 10px var(primary-color)` at low opacity).
- **Progress Bars:** Should look like a filling vessel, using a liquid-wave animation for the filling state.
- **Modals:** Centered overlays that use a "Deep Sea" backdrop blur (40px) to completely isolate the user from the background layers.