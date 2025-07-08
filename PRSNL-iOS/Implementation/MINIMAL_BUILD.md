# Minimal Build Instructions (No Extensions)

If you're still having issues, try building just the main app without extensions:

## Steps:

1. **In Xcode:**
   - Select PRSNL scheme (not extensions)
   - Edit Scheme → Build → Uncheck PRSNLShareExtension and PRSNLWidgets

2. **Update Bundle ID:**
   - Select PRSNL target
   - Change Bundle Identifier to: `com.yourname.prsnl`
   - Select your personal team
   - Enable "Automatically manage signing"

3. **Remove App Groups:**
   - In Signing & Capabilities
   - Click "−" next to App Groups

4. **Build & Run:**
   - Select iPhone Simulator
   - Product → Run (⌘R)

This will get the main app working first, then you can add extensions later.