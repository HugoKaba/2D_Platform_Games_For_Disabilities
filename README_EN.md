# 2D Platform Games For Disabilities (MiniMarioAR)

**MiniMarioAR** is an experimental 2D platformer designed to break through the barriers of digital interaction. This project explores how computer vision (AR) and speech recognition technologies can provide a full gaming experience for people with motor disabilities or reduced mobility.

![Game Menu](assets/screenshot/menu.png)

## 🌟 Vision & Inclusion
The goal of this project is to demonstrate that video games can be universal. By replacing or supplementing traditional keyboard controls with natural commands, MiniMarioAR allows everyone to immerse themselves in a playful universe, regardless of their degree of mobility.



## 🛠 Accessibility Features

### 1. Full Voice Control (Hands-Free)
The player can control the entire game without any physical contact. The engine uses Google Speech Recognition for optimal accuracy.

| Action | Voice Command (FR Support) |
| :--- | :--- |
| **Start Game** | "Jouer" |
| **Navigation** | "Menu", "Settings" |
| **Session Management** | "Pause", "Resume" (Reprendre), "Restart" (Rejouer) |
| **Level Selection** | "Niveau 1" to "Niveau 10" |
| **Control Modes** | "Mode Mixte", "Mode Clavier", "Mode Caméra" |
| **Quit** | "Quitter" |

> [!NOTE]
> Currently, the voice engine is optimized for French commands as listed above.

### 2. AR Gesture Control (Spatial Interface)
![Directional Mode](assets/screenshot/gameplay_directionel.png)
The webcam tracks your hand (or index/stump) position in real-time.
- **Spatial Interface**: The screen is divided into zones. Pointing up triggers a jump, down triggers an attack.
- **AR Radar**: A discreet monitor shows you exactly what the camera sees at all times.

### 3. Custom Settings
![Settings](assets/screenshot/param.png)
Four sensitivity profiles (**Easy, Normal, Hard, Special**) allow the game to be adjusted to each user's range of motion.

## 🎮 Classical Controls (Keyboard)
| Action | Key |
| :--- | :--- |
| **Move** | Left / Right Arrows (or Q/D) |
| **Jump** | Up Arrow / Space (or Z) |
| **Attack** | S Key |
| **Menu / Pause** | S / P / M Keys |

## 🚀 Getting Started

> [!IMPORTANT]
> An internet connection is required for voice recognition (Google Web API).

### Direct Launch
1. Download the archive matching your system.
2. **macOS**: Launch `MiniMarioAR.app`. If macOS blocks the app, go to *System Settings > Privacy & Security* and click **"Open Anyway"**.
3. **Windows**: Launch `MiniMarioAR.exe`.

## 🏗 Multi-Platform Build
Run the corresponding command in a **Bash** terminal:

| OS | Command | Note |
| :--- | :--- | :--- |
| **macOS** | `./build_macos.sh` | Generates a `.app` |
| **Windows** | `./build_windows.sh` | Use **Git Bash** |
| **Linux** | `./build_linux.sh` | Generates an ELF binary |

## ❓ Troubleshooting
> [!TIP]
> - **Camera not detected**: Ensure no other application is using the webcam. On macOS, check Security permissions.
> - **Voice lag**: Recognition depends on internet quality and microphone clarity.
> - **Unstable AR detection**: Try to be in a well-lit area with a uniform background.

---
*Project developed with a commitment to digital accessibility.*
