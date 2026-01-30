<img width="1830" height="1041" alt="Screenshot from 2026-01-30 16-47-54" src="https://github.com/user-attachments/assets/7efc8bf8-c541-4a08-af15-dd1c3abf7e52" />

# AppChino
# 🎥 AppChino v1.0 - Video Analyzer for Mandarin Learning

AppChino is an intelligent tool designed for Mandarin Chinese learners who want to study using real-world content. The application analyzes videos, extracts vocabulary, and categorizes every word according to official HSK levels, allowing users to instantly view video examples of how each word is used in context.

## 🚀 Current Features (v1.0)

- **Video Processing:** Downloads and transcribes videos (local or YouTube) using **OpenAI Whisper**.
- **Text Segmentation:** Implementation of `jieba` for precise Chinese word segmentation.
- **HSK Database:** Automatic classification of words into **HSK levels 1 to 6** (compatible with HSK 3.0) using a catalog of over 11,000 entries.
- **In-Video Example Finder:** Upon selecting a word, the app automatically locates and plays the specific video segments where that word is used.
- **Integrated Dictionary:** Definitions and pinyin provided via the **CEDICT** dictionary.
- **Graphical User Interface (PyQt5):** Intuitive organization with level-based tabs to facilitate progressive study.

## 🛠️ Requirements & Installation

### Prerequisites
- **Python 3.10+**
- **FFmpeg:** Essential for handling audio and video streams.

### Quick Installation
1. **Clone the repository:**
   ```bash
   git clone [https://github.com/Ivan2099-phy/AppChino.git](https://github.com/Ivan2099-phy/AppChino.git)
   cd AppChino
Automatic Configuration: Run the included script to create the virtual environment (venv), install dependencies, and launch the app:

Bash

chmod +x setup_and_run.sh
./setup_and_run.sh
📂 Project Structure
src/: Core logic for the analyzer and interface controllers.

src/data/: Reference files (HSK JSON and CEDICT Dictionary).

data/: Local storage for videos, audio, and the SQLite database chinese_video.db.

📈 Roadmap (Upcoming Features)
For version v1.1, the main focus will be on learning retention:

[ ] Anki Export: Automatic generation of flashcards featuring Hanzi, Pinyin, meaning, and the associated video example clip.

[ ] AI Audio (TTS): Integration of natural voices to hear the isolated pronunciation of each word.

[ ] AI Grammar Explanation: Connection to LLMs to analyze the grammatical structure of sentences detected in the videos.

🤝 Contributions
This project started as a personal tool to accelerate Mandarin fluency. If you have ideas to improve the segmentation algorithm or the user experience, contributions are more than welcome.

This Repo is for just for hobby.
