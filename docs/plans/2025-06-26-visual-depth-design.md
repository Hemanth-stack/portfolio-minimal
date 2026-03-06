# Visual Depth Design — "Hybrid Intelligence"

**Date**: 2025-06-26  
**Status**: Approved  
**Target Audience**: AI/ML technical leaders, CEOs, CTOs in AI industry  

## Summary

Add visual depth to the cream/navy portfolio theme using an SVG neural network animation in the hero section, layered shadow system throughout, and subtle micro-interactions. No palette change — enhances existing theme.

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Animation type | SVG neural network with CSS keyframes | No JS for animation, clean vectors, prints well |
| Animation scope | Hero section only | Keeps rest of site fast and clean |
| Color palette | Keep cream (#FFF8E7) + navy (#1B1464) + yellow (#E8DC3C) | User preference, maintains brand |
| Depth mechanism | Multi-layer box-shadows + gradient backgrounds | Physical depth without heaviness |
| JS footprint | ~10 lines for scroll reveal only | Minimal, progressive enhancement |

## Implementation Plan

### Phase 1: SVG Neural Network Hero Background

**Files**: `app/templates/index.html`, `static/style.css`

1. Add inline SVG element inside `.hero` section with `position: absolute` behind content
2. SVG contains:
   - 18 circle nodes: navy at 15% opacity, positioned across full width/height
   - 3 accent nodes: yellow (#E8DC3C) at 25% opacity
   - 28 connection lines between nearby nodes: navy at 8% opacity
3. CSS keyframes for node animation:
   - `@keyframes nodeFloat1`: translateX(10px) translateY(-15px) over 10s, alternate
   - `@keyframes nodeFloat2`: translateX(-12px) translateY(8px) over 13s, alternate
   - `@keyframes nodeFloat3`: translateX(8px) translateY(12px) over 8s, alternate
4. CSS keyframes for line pulse: opacity 0.05 → 0.15 over 6-10s, alternate
5. Hero section gets `position: relative; overflow: hidden`
6. Hero content gets `position: relative; z-index: 1`
7. Mobile: Media query hides ~8 nodes and their lines for performance

### Phase 2: Depth Shadow System

**Files**: `static/style.css`

1. Define shadow tokens:
   ```css
   --shadow-sm: 0 1px 2px rgba(27,20,100,0.04), 0 2px 4px rgba(27,20,100,0.04);
   --shadow-md: 0 1px 2px rgba(27,20,100,0.04), 0 4px 8px rgba(27,20,100,0.06), 0 12px 24px rgba(27,20,100,0.08);
   --shadow-lg: 0 2px 4px rgba(27,20,100,0.04), 0 8px 16px rgba(27,20,100,0.08), 0 24px 48px rgba(27,20,100,0.12);
   --shadow-glow: 0 0 40px rgba(27,20,100,0.12), 0 0 80px rgba(232,220,60,0.06);
   ```
2. Apply to components:
   - `.project-card`: `box-shadow: var(--shadow-md)`, remove border, add `background: var(--bg)`
   - `.project-card:hover`: `box-shadow: var(--shadow-lg); transform: translateY(-4px) scale(1.02)`
   - `.section-cta .section-content`: `box-shadow: var(--shadow-md)`
   - `.modal-content`: `box-shadow: var(--shadow-lg)`
   - `.inline-editor`: `box-shadow: var(--shadow-sm)`

### Phase 3: Section Backgrounds & Dividers

**Files**: `static/style.css`

1. Alternating section backgrounds:
   - `.section-what-i-do`: `background: linear-gradient(135deg, var(--bg) 0%, var(--bg-alt) 100%); border-radius: 16px; padding: 3rem 2rem;`
   - `.section-projects`: same pattern
2. Gradient dividers — replace hard `border-bottom` on section headings with:
   ```css
   .section-recent h2::after, .section-projects h2::after {
     content: '';
     display: block;
     height: 2px;
     margin-top: 0.75rem;
     background: linear-gradient(90deg, var(--fg), var(--border), transparent);
   }
   ```
   Remove `border-bottom` from these headings.
3. Footer: gradient top border instead of solid:
   ```css
   footer { border-image: linear-gradient(90deg, transparent, var(--border), transparent) 1; }
   ```

### Phase 4: Hero Photo Enhancement

**Files**: `static/style.css`

1. Glow effect on `.hero-photo`:
   ```css
   box-shadow: 0 0 40px rgba(27,20,100,0.15), 0 0 80px rgba(232,220,60,0.08);
   ```
2. Animated decorative ring (`.hero-photo-wrapper::before`):
   - Change to `border: 2px dashed var(--border)`
   - Add `@keyframes ringRotate { to { transform: translate(-48%, -52%) rotate(360deg); } }`
   - Apply `animation: ringRotate 60s linear infinite`

### Phase 5: Micro-interactions

**Files**: `static/style.css`, `app/templates/base.html`

1. **Link underline slide** — nav links and content links:
   ```css
   .nav-links a { position: relative; }
   .nav-links a::after {
     content: ''; position: absolute; bottom: -2px; left: 0;
     width: 0; height: 2px; background: var(--accent);
     transition: width 0.3s ease;
   }
   .nav-links a:hover::after { width: 100%; }
   ```
2. **Scroll reveal** — add to base.html:
   ```html
   <script>
   document.addEventListener('DOMContentLoaded', () => {
     const obs = new IntersectionObserver((entries) => {
       entries.forEach(e => { if (e.isIntersecting) { e.target.classList.add('revealed'); obs.unobserve(e.target); } });
     }, { threshold: 0.1 });
     document.querySelectorAll('.reveal-on-scroll').forEach(el => obs.observe(el));
   });
   </script>
   ```
   ```css
   .reveal-on-scroll { opacity: 0; transform: translateY(20px); transition: opacity 0.6s ease, transform 0.6s ease; }
   .revealed { opacity: 1; transform: translateY(0); }
   ```
3. Add `.reveal-on-scroll` class to sections in `index.html`: `.section-what-i-do`, `.section-recent`, `.section-projects`, `.section-cta`

### Phase 6: CSS Cache Bust

**Files**: `app/templates/base.html`

- Bump `style.css?v=4` → `style.css?v=5`

## Files Modified

| File | Changes |
|------|---------|
| `static/style.css` | Shadow tokens, keyframes, depth shadows, gradient dividers, photo glow, micro-interactions, reveal animation |
| `app/templates/index.html` | Inline SVG neural network, `.reveal-on-scroll` classes on sections |
| `app/templates/base.html` | Scroll reveal JS snippet, CSS version bump to v5 |

## Mobile Considerations

- SVG neural network: hide ~8 of 21 nodes on screens < 768px via `display: none` on `.nn-hide-mobile`
- Shadow system: reduce shadow intensity on mobile for performance
- Scroll reveal: works natively with IntersectionObserver (wide browser support)
- No performance-heavy animations — all CSS, no requestAnimationFrame

## Accessibility

- SVG neural network has `aria-hidden="true"` and `role="presentation"`
- Respects `prefers-reduced-motion`: disables all animations
- All depth enhancements are visual only — no semantic changes
