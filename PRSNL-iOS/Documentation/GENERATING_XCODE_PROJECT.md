# Generating the Xcode Project for PRSNL

The PRSNL iOS app uses XcodeGen to generate the Xcode project file from a configuration file. This guide explains how to generate the .xcodeproj file from the project.yml file.

## Current Status

Right now, you have the `project.yml` file but not the actual Xcode project file (`.xcodeproj`). The project.yml file is the configuration that XcodeGen uses to generate the Xcode project.

- Configuration file: `/Users/pronav/Personal Knowledge Base/PRSNL-iOS/Implementation/project.yml`
- Xcode project to be generated: `/Users/pronav/Personal Knowledge Base/PRSNL-iOS/Implementation/PRSNL.xcodeproj`

## Steps to Generate the Xcode Project

1. **Install XcodeGen** (if not already installed):
   ```bash
   brew install xcodegen
   ```

2. **Navigate to the Implementation directory**:
   ```bash
   cd /Users/pronav/Personal Knowledge Base/PRSNL-iOS/Implementation
   ```

3. **Run XcodeGen**:
   ```bash
   xcodegen generate
   ```

4. **Open the generated project**:
   ```bash
   open PRSNL.xcodeproj
   ```

## Alternative: Use the Provided Script

We've created a shell script that automates this process:

1. **Make the script executable**:
   ```bash
   chmod +x /Users/pronav/Personal Knowledge Base/PRSNL-iOS/Implementation/generate_project.sh
   ```

2. **Run the script**:
   ```bash
   cd /Users/pronav/Personal Knowledge Base/PRSNL-iOS/Implementation
   ./generate_project.sh
   ```

The script will:
- Check if XcodeGen is installed (and install it if needed)
- Clean up any existing project files
- Generate the new Xcode project
- Provide a success message with next steps

## After Generating the Project

Once the Xcode project is generated:

1. Open the project in Xcode
2. Configure signing with your Apple ID
3. Connect your iPhone
4. Build and run on your device

Follow the detailed instructions in `TRANSFER_TO_IPHONE_GUIDE.md` for the complete process of getting the app onto your iPhone.

## Troubleshooting

If you encounter issues generating the project:

1. **XcodeGen not found**: Make sure you've installed XcodeGen using Homebrew
2. **Validation errors**: Check the project.yml file for any syntax errors
3. **Permission denied**: Make sure the script is executable (`chmod +x generate_project.sh`)