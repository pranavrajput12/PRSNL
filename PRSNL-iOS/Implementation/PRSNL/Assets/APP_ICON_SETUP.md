# PRSNL App Icon Setup Guide

## App Icon Design
The app icon has been created with:
- Manchester United red gradient background (#DC143C)
- Neural network pattern overlay
- Central brain symbol representing knowledge
- Orbiting knowledge dots
- PRSNL text at bottom

## Required Icon Sizes

### iOS App Icons
Create these sizes from the AppIconView:
- 20x20 (2x, 3x) - Notification
- 29x29 (2x, 3x) - Settings
- 40x40 (2x, 3x) - Spotlight
- 60x60 (2x, 3x) - App Icon
- 1024x1024 - App Store

### Share Extension Icon
The share extension uses the same design but without the "PRSNL" text.

## How to Generate Icons

1. **Using SwiftUI Preview**:
```swift
// In AppIconView.swift preview
AppIconView(size: 1024)
    .background(Color.clear)
```

2. **Export from Xcode**:
- Run the app in simulator
- Use the preview to capture at different sizes
- Or use an icon generator tool

3. **Add to Assets.xcassets**:
- Open `Assets.xcassets`
- Create new "AppIcon" image set
- Drag generated icons to appropriate slots

## Icon Specifications
- Format: PNG
- Color Space: sRGB
- No transparency for App Store icon
- Corner radius applied automatically by iOS

## Alternative: Using SF Symbols
For a quick implementation, you can use SF Symbols:
```swift
Image(systemName: "brain")
    .symbolRenderingMode(.hierarchical)
    .foregroundStyle(.red)
```

## Launch Screen Setup
The launch screen is implemented as a SwiftUI view with:
- Animated neural brain visualization
- Pulsing circles effect
- Floating knowledge particles
- Loading progress indicator
- Typewriter text effect

No additional setup needed - it's integrated into PRSNLApp.swift!