# echomatrix


Voice-driven AI IVR system using FreePBX, Asterisk, and OpenAI APIs.

## 🔧 Features

- Whisper for speech-to-text
- GPT-4 Turbo for smart responses
- OpenAI TTS for fast, high-quality voice replies
- Modular Python design with AGI integration

## 🚀 Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
sudo dnf install mpg123  alsa-utils 
# you need to install sox. IT might requre a build from scratch and you need a lot of dependencies to get mp3 etcv working.

wget    https://cytranet-dal.dl.sourceforge.net/project/sox/sox/14.4.2/sox-14.4.2.tar.bz2
tar -xvjf sox-14.4.2.tar.bz2 sox-14.4.2/
cd sox-14.4.2/
dnf install  'lame'* 'flac*' 'libsox*'
dnf install opencore-amr-devel libid3tag-devel libmad-devel twolame-devel \
            libvorbis-devel opus-devel libsndfile-devel wavpack-devel file-devel libpng-devel
  
# you need to add #include <math.h> to this file on line 23
vi src/sox_sample_test.h

./configure
make -s && make install
```
