# InstaSend

InstaSend is a desktop application designed for automating Instagram Direct Messages (DM). It provides a graphical user interface to manage account profiles and control the automated sending workflow.

## Platform Support

Currently, InstaSend officially supports Windows only.

## Key Features

- **Account Management**: Save and manage multiple Instagram profiles and configurations.
- **Automated Messaging**: Send direct messages to target users automatically.
- **Flexible Intervals**: Supports both fixed and randomized delay intervals to mimic human behavior.

## Sending Modes

- **Single Send**: Sends a single direct message to the target user and then stops.
- **Multiple Send**: Sends a specific number of messages defined by the user.
- **Infinite Send**: Continually sends messages until the process is manually stopped.

## Installation

Pre-compiled installation files are available in the Releases section of this repository. You can download and run InstaSend-Setup.exe to install the application on your system.

## Build from Source (Windows)

To build InstaSend from the source code, follow the instructions below.

### Prerequisites

1. Python and uv: The project uses uv for dependency management.
2. Inno Setup: Required for generating the setup installer. Ensure that the Inno Setup compiler (iscc) is added to your system PATH.

### Build Instructions

1. Clone this repository to your local machine.
2. Open a terminal or command prompt in the project root directory.
3. Run the setup script to initialize the environment and install necessary dependencies:
   ```cmd
   setup.bat
   ```
4. Run the build script to compile the application and generate the installer:
   ```cmd
   build.bat
   ```

After the process completes, the standalone installer InstaSend-Setup.exe will be located in the project root directory.

## Disclaimer

This automated tool is provided for entertainment purposes only. The developer is not responsible for any account bans or restrictions imposed by Instagram. Users assume all responsibility and risk associated with the use of this software.
