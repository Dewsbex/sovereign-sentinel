# ⚡ CLOUDFLARE QUICK REFERENCE

## Zero-Build Configuration

### Settings → Builds & deployments → Configure Production Build

```
Build command:              [EMPTY - DELETE EVERYTHING]
Build output directory:     /
Root directory:             /
Framework preset:           None
```

## The Static Hand-off Principle

```
┌─────────────────────────────────────────────────────────┐
│  GITHUB ACTIONS (The Engine)                            │
│  ├─ Runs at 14:25 UTC Mon-Fri                          │
│  ├─ pip install -r requirements.txt                     │
│  ├─ python generate_ui.py                               │
│  ├─ Creates index.html with Industrial Vibe            │
│  └─ git commit + push                                   │
│                          ↓                               │
│  CLOUDFLARE PAGES (The Host)                            │
│  ├─ Detects new commit                                  │
│  ├─ NO BUILD - just grab index.html                    │
│  └─ Deploy to *.pages.dev                              │
└─────────────────────────────────────────────────────────┘
```

## Industrial Vibe Aesthetic Verification

Once deployed, verify these features render correctly:

### ✅ Visual Tokens
- **Background:** True black `#000000`
- **Borders:** 1px solid `#333` / `#444`
- **Typography:** JetBrains Mono, all-caps
- **No curves:** `border-radius: 0px` everywhere

### ✅ Inverted Momentum Heatmap
- **Small moves** (+/-0.1-1%) → Bright pastels (mint `#d1fae5`, rose `#fee2e2`)
- **Large moves** (>3%) → Deep solids (forest `#064e3b`, blood `#7f1d1d`)
- **Height:** Fixed 550px

### ✅ Sector Power-Grid
- **Left (1/3):** Asset donut with SVG labels
- **Right (2/3):** Horizontal bars with dotted target lines
- **Labels:** OVER (red), UNDER (yellow), MATCH (green)

### ✅ Header (Sticky)
- Market phase display: `PHASE: MID-BULL`
- Fortress alert banner (if triggered)
- Wealth, P/L, status metrics

## Deployment URL

After successful deployment:
```
https://[your-project-name].pages.dev
```

## Troubleshooting

**If build fails:**
1. Check build command is EMPTY
2. Verify output directory is `/`
3. Retry deployment from Deployments tab

**If dashboard doesn't update:**
1. GitHub Action runs at 14:25 UTC Mon-Fri
2. Manual trigger: Actions → Run workflow
3. Cloudflare auto-deploys on new commit

## Success Criteria

✅ Deployment status: SUCCESS  
✅ Build time: <10 seconds (no Python install)  
✅ Dashboard loads at *.pages.dev  
✅ Industrial Vibe renders correctly  
✅ Heatmap shows with inverted colors  
✅ Sector bars display with target lines  

---

**The Ghost Sovereign awaits at your Cloudflare URL.** 🚀
