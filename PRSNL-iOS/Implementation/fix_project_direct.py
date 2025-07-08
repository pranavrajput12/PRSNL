#!/usr/bin/env python3
"""
This script directly modifies the Xcode project to fix signing issues
"""
import os
import re
import plistlib

def fix_pbxproj():
    """Remove code signing requirements from project.pbxproj"""
    pbxproj_path = "PRSNL.xcodeproj/project.pbxproj"
    
    if not os.path.exists(pbxproj_path):
        print(f"❌ {pbxproj_path} not found")
        return False
    
    print(f"📝 Modifying {pbxproj_path}...")
    
    with open(pbxproj_path, 'r') as f:
        content = f.read()
    
    # Remove/disable code signing
    replacements = [
        # Remove team references
        (r'DevelopmentTeam = [A-Z0-9]+;', 'DevelopmentTeam = "";'),
        (r'DEVELOPMENT_TEAM = [A-Z0-9]+;', 'DEVELOPMENT_TEAM = "";'),
        
        # Disable code signing for debug
        (r'CODE_SIGN_IDENTITY = ".*?";', 'CODE_SIGN_IDENTITY = "";'),
        (r'CODE_SIGNING_REQUIRED = YES;', 'CODE_SIGNING_REQUIRED = NO;'),
        
        # Remove provisioning profiles
        (r'PROVISIONING_PROFILE = ".*?";', 'PROVISIONING_PROFILE = "";'),
        (r'PROVISIONING_PROFILE_SPECIFIER = ".*?";', 'PROVISIONING_PROFILE_SPECIFIER = "";'),
        
        # Update bundle identifiers to local ones
        (r'PRODUCT_BUNDLE_IDENTIFIER = ai\.prsnl;', 'PRODUCT_BUNDLE_IDENTIFIER = com.local.prsnl;'),
        (r'PRODUCT_BUNDLE_IDENTIFIER = ai\.prsnl\.shareextension;', 'PRODUCT_BUNDLE_IDENTIFIER = com.local.prsnl.shareextension;'),
        (r'PRODUCT_BUNDLE_IDENTIFIER = ai\.prsnl\.widgets;', 'PRODUCT_BUNDLE_IDENTIFIER = com.local.prsnl.widgets;'),
    ]
    
    modified = content
    for pattern, replacement in replacements:
        modified = re.sub(pattern, replacement, modified)
    
    # Add simulator-only build settings if not present
    if 'EXCLUDED_ARCHS' not in modified:
        # Find a good place to insert (after PRODUCT_NAME usually)
        insert_point = modified.find('PRODUCT_NAME = ')
        if insert_point > 0:
            # Find the end of that line
            line_end = modified.find('\n', insert_point)
            if line_end > 0:
                insert_text = '''
				EXCLUDED_ARCHS = "";
				"EXCLUDED_ARCHS[sdk=iphonesimulator*]" = arm64;
				ONLY_ACTIVE_ARCH = YES;
				VALID_ARCHS = "arm64 x86_64";
'''
                modified = modified[:line_end] + insert_text + modified[line_end:]
    
    with open(pbxproj_path, 'w') as f:
        f.write(modified)
    
    print("✅ project.pbxproj modified")
    return True

def create_schemes():
    """Create simulator-only schemes"""
    schemes_dir = "PRSNL.xcodeproj/xcshareddata/xcschemes"
    os.makedirs(schemes_dir, exist_ok=True)
    
    scheme_content = '''<?xml version="1.0" encoding="UTF-8"?>
<Scheme
   LastUpgradeVersion = "1540"
   version = "1.3">
   <BuildAction
      parallelizeBuildables = "YES"
      buildImplicitDependencies = "YES">
      <BuildActionEntries>
         <BuildActionEntry
            buildForTesting = "YES"
            buildForRunning = "YES"
            buildForProfiling = "YES"
            buildForArchiving = "YES"
            buildForAnalyzing = "YES">
            <BuildableReference
               BuildableIdentifier = "primary"
               BlueprintIdentifier = "TARGETID"
               BuildableName = "PRSNL.app"
               BlueprintName = "PRSNL"
               ReferencedContainer = "container:PRSNL.xcodeproj">
            </BuildableReference>
         </BuildActionEntry>
      </BuildActionEntries>
   </BuildAction>
   <TestAction
      buildConfiguration = "Debug"
      selectedDebuggerIdentifier = "Xcode.DebuggerFoundation.Debugger.LLDB"
      selectedLauncherIdentifier = "Xcode.DebuggerFoundation.Launcher.LLDB"
      shouldUseLaunchSchemeArgsEnv = "YES">
   </TestAction>
   <LaunchAction
      buildConfiguration = "Debug"
      selectedDebuggerIdentifier = "Xcode.DebuggerFoundation.Debugger.LLDB"
      selectedLauncherIdentifier = "Xcode.DebuggerFoundation.Launcher.LLDB"
      launchStyle = "0"
      useCustomWorkingDirectory = "NO"
      ignoresPersistentStateOnLaunch = "NO"
      debugDocumentVersioning = "YES"
      debugServiceExtension = "internal"
      allowLocationSimulation = "YES">
      <BuildableProductRunnable
         runnableDebuggingMode = "0">
         <BuildableReference
            BuildableIdentifier = "primary"
            BlueprintIdentifier = "TARGETID"
            BuildableName = "PRSNL.app"
            BlueprintName = "PRSNL"
            ReferencedContainer = "container:PRSNL.xcodeproj">
         </BuildableReference>
      </BuildableProductRunnable>
      <EnvironmentVariables>
         <EnvironmentVariable
            key = "CODE_SIGNING_REQUIRED"
            value = "NO"
            isEnabled = "YES">
         </EnvironmentVariable>
      </EnvironmentVariables>
   </LaunchAction>
   <ProfileAction
      buildConfiguration = "Release"
      shouldUseLaunchSchemeArgsEnv = "YES"
      savedToolIdentifier = ""
      useCustomWorkingDirectory = "NO"
      debugDocumentVersioning = "YES">
   </ProfileAction>
   <AnalyzeAction
      buildConfiguration = "Debug">
   </AnalyzeAction>
   <ArchiveAction
      buildConfiguration = "Release"
      revealArchiveInOrganizer = "YES">
   </ArchiveAction>
</Scheme>'''
    
    with open(f"{schemes_dir}/PRSNL-Simulator.xcscheme", 'w') as f:
        f.write(scheme_content)
    
    print("✅ Created simulator scheme")

def fix_entitlements():
    """Remove problematic entitlements"""
    entitlements_files = [
        "PRSNL/PRSNL.entitlements",
        "PRSNLShareExtension/PRSNLShareExtension.entitlements",
        "PRSNLWidgets/PRSNLWidgets.entitlements"
    ]
    
    for file in entitlements_files:
        if os.path.exists(file):
            print(f"📝 Fixing {file}...")
            # Create minimal entitlements
            minimal_entitlements = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict/>
</plist>'''
            with open(file, 'w') as f:
                f.write(minimal_entitlements)
    
    print("✅ Entitlements fixed")

def main():
    print("🔧 Fixing PRSNL Xcode Project...")
    print("=" * 50)
    
    # Change to project directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Fix project file
    if not fix_pbxproj():
        return
    
    # Fix entitlements
    fix_entitlements()
    
    # Create schemes
    create_schemes()
    
    print("\n✅ All fixes applied!")
    print("\nNext steps:")
    print("1. Close Xcode completely")
    print("2. Delete ~/Library/Developer/Xcode/DerivedData/PRSNL-*")
    print("3. Open PRSNL.xcodeproj again")
    print("4. Select iPhone Simulator as target")
    print("5. Build and run (Cmd+R)")
    print("\nIf you still see errors:")
    print("- Try Product > Clean Build Folder")
    print("- Select only the PRSNL scheme (not extensions)")

if __name__ == "__main__":
    main()